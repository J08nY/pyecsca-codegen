#!/usr/bin/env python3
import re
from binascii import hexlify, unhexlify
from enum import IntFlag
from os import path
from time import time
from typing import Mapping, Union, Optional, Tuple

import chipwhisperer as cw
import click
from chipwhisperer.capture.api.programmers import STM32FProgrammer, XMEGAProgrammer
from chipwhisperer.capture.targets import SimpleSerial
from public import public
from pyecsca.ec.coordinates import CoordinateModel, AffineCoordinateModel
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import CurveModel
from pyecsca.ec.params import DomainParameters, get_params
from pyecsca.ec.point import Point, InfinityPoint
from pyecsca.sca.target import (SimpleSerialTarget, ChipWhispererTarget, BinaryTarget, Flashable,
                                SimpleSerialMessage as SMessage)

from .common import wrap_enum, Platform, get_model, get_coords


class Triggers(IntFlag):
    """
    Actions that the implementation can trigger on.

    Given that this is a bit-flag, multiple choices are
    allowed, in which case the trigger signal will toggle
    onn each action entry/exit.
    """
    add = 1 << 0
    dadd = 1 << 1
    dbl = 1 << 2
    ladd = 1 << 3
    neg = 1 << 4
    scl = 1 << 5
    tpl = 1 << 6
    mult = 1 << 7
    keygen = 1 << 8
    ecdh = 1 << 9
    ecdsa_sign = 1 << 10
    ecdsa_verify = 1 << 11
    coord_map = 1 << 12
    random_mod = 1 << 13


def encode_scalar(val: Union[int, Mod]) -> bytes:
    """
    Encode a scalar value (int or Mod) into bytes,
    such that the implementation can load them.
    """
    if isinstance(val, int):
        return val.to_bytes((val.bit_length() + 7) // 8, "big")
    elif isinstance(val, Mod):
        return encode_scalar(int(val))
    return bytes()


def encode_point(point: Point) -> Mapping:
    """
    Encode point coordinates.
    """
    if isinstance(point, InfinityPoint):
        return {"n": bytes([1])}
    return {var: encode_scalar(value) for var, value in point.coords.items()}


def encode_data(name: Optional[str], structure: Union[Mapping, bytes]) -> bytes:
    """
    Encode `structure` into the format used by the implementation command
    parsing (see <docs/commands.rst>) and give it a `name`.

    The format uses a tree of name-length-value nodes that is serialized
    one after another (and can be easily parsed out recursively). This function
    expects the `structure` to be either:
      - bytes, in which case this is a leaf node and the function will just
      create the name-length-value entry encoding.
      - Mapping, in which case this function will recursively encode the
      entries in the mapping.
    """
    if isinstance(structure, bytes):
        if name is None:
            raise ValueError
        header = bytes([ord(name)]) + bytes([len(structure)])
        return header + structure
    data = bytes()
    for k, v in structure.items():
        data += encode_data(k, v)
    if name is not None:
        return bytes([ord(name) | 0x80]) + bytes([len(data)]) + data
    return data


def decode_data(data: bytes) -> Mapping:
    """
    Decode the `data` in the format used by the implementation command
    parsing.

    The format uses a tree of name-length-value nodes, this tree is
    deserialized and turned into a Mapping by this function. However,
    as the format does not hold any information about the data type
    (only its name, length and value) this function does not decode
    the byte values (i.e. decoding an encoding of a scalar will
    result in a Mapping with bytes on the output, not an int or a Mod).
    """
    result = {}
    parsed = 0
    while parsed < len(data):
        name = data[parsed]
        length = data[parsed + 1]
        if name & 0x80:
            sub = decode_data(data[parsed + 2: parsed + 2 + length])
            result[chr(name & 0x7f)] = sub
            parsed += length + 2
        else:
            result[chr(name)] = data[parsed + 2: parsed + 2 + length]
            parsed += length + 2
    return result


@public
def cmd_init_prng(seed: bytes) -> str:
    return "i" + hexlify(seed).decode()


@public
def cmd_set_params(params: DomainParameters) -> str:
    data = {
        "p": encode_scalar(params.curve.prime),
        "n": encode_scalar(params.order),
        "h": encode_scalar(params.cofactor)
    }
    for param, value in params.curve.parameters.items():
        data[param] = encode_scalar(value)
    data["g"] = encode_point(params.generator.to_affine())
    data["i"] = encode_point(params.curve.neutral)
    return "c" + hexlify(encode_data(None, data)).decode()


@public
def cmd_generate() -> str:
    return "g"


@public
def cmd_set_privkey(privkey: int) -> str:
    return "s" + hexlify(encode_data(None, {"s": encode_scalar(privkey)})).decode()


@public
def cmd_set_pubkey(pubkey: Point) -> str:
    return "w" + hexlify(encode_data(None, {"w": encode_point(pubkey.to_affine())})).decode()


@public
def cmd_scalar_mult(scalar: int, point: Point) -> str:
    return "m" + hexlify(encode_data(None, {"s": encode_scalar(scalar),
                                            "w": encode_point(point.to_affine())})).decode()


@public
def cmd_ecdh(pubkey: Point) -> str:
    return "e" + hexlify(encode_data(None, {"w": encode_point(pubkey.to_affine())})).decode()


@public
def cmd_ecdsa_sign(data: bytes) -> str:
    return "a" + hexlify(encode_data(None, {"d": data})).decode()


@public
def cmd_ecdsa_verify(data: bytes, sig: bytes) -> str:
    return "r" + hexlify(encode_data(None, {"d": data, "s": sig})).decode()


@public
def cmd_set_trigger(actions: Triggers) -> str:
    vector_bytes = actions.to_bytes(4, "little")
    return "t" + hexlify(vector_bytes).decode()


@public
def cmd_debug() -> str:
    return "d"


class ImplTarget(SimpleSerialTarget):
    """
    A target that is based on an implementation built by pyecsca-codegen.

    This is an abstract class that uses the send_cmd method on the SimpleSerialTarget
    class to send commands to the target. That class in turn requires one to
    implement the read/write/connect/disconnect methods that communicate with the
    target somehow. See `DeviceTarget` that uses `ChipWhispererTarget` for thar purpose,
    or `HostTarget` that uses `BinaryTarget`.
    """
    model: CurveModel
    coords: CoordinateModel
    seed: Optional[bytes]
    params: Optional[DomainParameters]
    privkey: Optional[int]
    pubkey: Optional[Point]
    trigger: Optional[Triggers]
    timeout: int

    def __init__(self, model: CurveModel, coords: CoordinateModel, **kwargs):
        super().__init__(**kwargs)
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
        else:
            self.timeout = 1000
        self.model = model
        self.coords = coords
        self.seed = None
        self.params = None
        self.privkey = None
        self.pubkey = None
        self.trigger = None

    def init_prng(self, seed: bytes) -> None:
        self.send_cmd(SMessage.from_raw(cmd_init_prng(seed)), self.timeout)
        self.seed = seed

    def set_params(self, params: DomainParameters) -> None:
        self.send_cmd(SMessage.from_raw(cmd_set_params(params)), self.timeout)
        self.params = params

    def generate(self) -> Tuple[int, Point]:
        resp = self.send_cmd(SMessage.from_raw(cmd_generate()), self.timeout)
        priv = resp["s"].data
        pub = resp["w"].data
        self.privkey = int(priv, 16)
        pub_len = len(pub)
        x = int(pub[:pub_len // 2], 16)
        y = int(pub[pub_len // 2:], 16)
        self.pubkey = Point(AffineCoordinateModel(self.model), x=Mod(x, self.params.curve.prime),
                            y=Mod(y, self.params.curve.prime))
        return self.privkey, self.pubkey

    def set_privkey(self, privkey: int) -> None:
        self.send_cmd(SMessage.from_raw(cmd_set_privkey(privkey)), self.timeout)
        self.privkey = privkey

    def set_pubkey(self, pubkey: Point) -> None:
        self.send_cmd(SMessage.from_raw(cmd_set_pubkey(pubkey)), self.timeout)
        self.pubkey = pubkey

    def scalar_mult(self, scalar: int, point: Point) -> Point:
        resp = self.send_cmd(SMessage.from_raw(cmd_scalar_mult(scalar, point)), self.timeout)
        result = resp["w"]
        plen = ((self.params.curve.prime.bit_length() + 7) // 8) * 2
        params = {var: Mod(int(result.data[i * plen:(i + 1) * plen], 16), self.params.curve.prime)
                  for
                  i, var in enumerate(self.coords.variables)}
        return Point(self.coords, **params)

    def ecdh(self, other_pubkey: Point) -> bytes:
        resp = self.send_cmd(SMessage.from_raw(cmd_ecdh(other_pubkey)), self.timeout)
        result = resp["r"]
        return unhexlify(result.data)

    def ecdsa_sign(self, data: bytes) -> bytes:
        resp = self.send_cmd(SMessage.from_raw(cmd_ecdsa_sign(data)), self.timeout)
        signature = resp["s"]
        return unhexlify(signature.data)

    def ecdsa_verify(self, data: bytes, signature: bytes) -> bool:
        resp = self.send_cmd(SMessage.from_raw(cmd_ecdsa_verify(data, signature)), self.timeout)
        result = resp["v"]
        return unhexlify(result.data)[0] == 1

    def debug(self) -> Tuple[str, str]:
        resp = self.send_cmd(SMessage.from_raw(cmd_debug()), self.timeout)["d"]
        model, coords = unhexlify(resp.data).decode().split(",")
        return model, coords

    def set_trigger(self, actions: Triggers) -> None:
        self.send_cmd(SMessage.from_raw(cmd_set_trigger(actions)), self.timeout)
        self.trigger = actions

    def quit(self):
        self.write(b"x\n")

    def disconnect(self):
        super().disconnect()


@public
class DeviceTarget(ImplTarget, ChipWhispererTarget):  # pragma: no cover
    """
    A ChipWhisperer-based device target.
    """

    def __init__(self, model: CurveModel, coords: CoordinateModel, platform: Platform, **kwargs):
        scope = cw.scope()
        scope.default_setup()
        target = SimpleSerial()
        if platform in (Platform.STM32F0, Platform.STM32F3):
            programmer = STM32FProgrammer
        elif platform == Platform.XMEGA:
            programmer = XMEGAProgrammer
        else:
            raise ValueError
        super().__init__(model, coords, target=target, scope=scope, programmer=programmer, **kwargs)


@public
class HostTarget(ImplTarget, BinaryTarget):
    """
    A host-based target, will just run the binary on your machine and communicate
    with it via stdin/stdout.
    """

    def __init__(self, model: CurveModel, coords: CoordinateModel, **kwargs):
        super().__init__(model, coords, **kwargs)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--platform", envvar="PLATFORM", required=True,
              type=click.Choice(Platform.names()),
              callback=wrap_enum(Platform),
              help="The target platform to use.")
@click.option("--fw",
              help="The firmware. Either a .hex file for a device platform or .elf for HOST platform.",
              required=True)
@click.option("--timeout", type=int, default=15000)
@click.argument("model", required=True,
                type=click.Choice(["shortw", "montgom", "edwards", "twisted"]),
                callback=get_model)
@click.argument("coords", required=True,
                callback=get_coords)
@click.version_option()
@click.pass_context
@public
def main(ctx, platform, fw, timeout, model, coords):
    """
    A tool for communicating with built and flashed ECC implementations.
    """
    ctx.ensure_object(dict)
    ctx.obj["fw"] = fw
    if platform != Platform.HOST:
        ctx.obj["target"] = DeviceTarget(model, coords, platform, timeout=timeout)
    else:
        if fw is None or not path.isfile(fw):
            click.secho("Binary is required if the target is the host.", fg="red", err=True)
            raise click.Abort
        ctx.obj["target"] = HostTarget(model, coords, binary=fw, timeout=timeout)


def get_curve(ctx: click.Context, param, value: Optional[str]) -> DomainParameters:
    if value is None:
        return None
    ctx.ensure_object(dict)
    category, name = value.split("/")
    curve = get_params(category, name, ctx.obj["coords"].name)
    ctx.obj["params"] = curve
    return curve


@main.command("gen")
@click.argument("curve", required=True, callback=get_curve)
@click.pass_context
@public
def generate(ctx: click.Context, curve):
    """Generate a keypair on a curve."""
    ctx.ensure_object(dict)
    target: ImplTarget = ctx.obj["target"]
    if isinstance(target, Flashable):
        target.flash(ctx.obj["fw"])
    target.connect()
    target.set_params(curve)
    start = time()
    click.echo(target.generate())
    click.echo(time() - start)
    target.quit()
    target.disconnect()


def get_pubkey(ctx: click.Context, param, value: Optional[str]) -> Point:
    if value is None:
        return None
    ctx.ensure_object(dict)
    curve: DomainParameters = ctx.obj["params"]
    if re.match("^04([0-9a-fA-F]{2})+$", value):
        value = value[2:]
        plen = len(value) // 2
        x = int(value[:plen], 16)
        y = int(value[plen:], 16)
    elif re.match("^[0-9]+,[0-9]+$", value):
        xs, ys = value.split(",")
        x = int(xs)
        y = int(ys)
    else:
        raise click.BadParameter("Couldn't parse pubkey: {}.".format(value))
    x = Mod(x, curve.curve.prime)
    y = Mod(y, curve.curve.prime)
    return Point(AffineCoordinateModel(curve.curve.model), x=x, y=y)


@main.command("ecdh")
@click.argument("curve", required=True, callback=get_curve)
@click.argument("pubkey", required=True, callback=get_pubkey)
@click.pass_context
@public
def ecdh(ctx: click.Context, curve, pubkey):
    """Perform ECDH with a given public key."""
    ctx.ensure_object(dict)
    target: ImplTarget = ctx.obj["target"]
    if isinstance(target, Flashable):
        target.flash(ctx.obj["fw"])
    target.connect()
    target.set_params(curve)
    target.generate()
    click.echo(hexlify(target.ecdh(pubkey)))
    target.quit()
    target.disconnect()


@main.command("ecdsa-sign")
@click.argument("curve", required=True, callback=get_curve)
@click.pass_context
@public
def ecdsa_sign(ctx: click.Context, curve):
    ctx.ensure_object(dict)
    # TODO
    click.echo("Not implemented.")


@main.command("ecdsa-verify")
@click.argument("curve", required=True, callback=get_curve)
@click.pass_context
@public
def ecdsa_verify(ctx: click.Context, curve):
    ctx.ensure_object(dict)
    # TODO
    click.echo("Not implemented.")


if __name__ == "__main__":
    main(obj={})
