#!/usr/bin/env python3
import subprocess
from binascii import hexlify, unhexlify
from os import path
from subprocess import Popen
from typing import Mapping, Union, Optional, Tuple

import click
from public import public
from pyecsca.ec.coordinates import CoordinateModel, AffineCoordinateModel
from pyecsca.ec.curves import get_params
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import CurveModel
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point, InfinityPoint
from pyecsca.sca import SerialTarget

from .common import wrap_enum, Platform, get_model, get_coords


def encode_scalar(val: Union[int, Mod]) -> bytes:
    if isinstance(val, int):
        return val.to_bytes((val.bit_length() + 7) // 8, "big")
    elif isinstance(val, Mod):
        return encode_scalar(int(val))
    return bytes()


def encode_point(point: Point) -> Mapping:
    if isinstance(point, InfinityPoint):
        return {"n": bytes([1])}
    return {var: encode_scalar(value) for var, value in point.coords.items()}


def encode_data(name: Optional[str], structure: Union[Mapping, bytes]) -> bytes:
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
def cmd_scalar_mult(scalar: int) -> str:
    return "m" + hexlify(encode_data(None, {"s": encode_scalar(scalar)})).decode()


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
def cmd_debug() -> str:
    return "d"


class ImplTarget(SerialTarget):
    model: CurveModel
    coords: CoordinateModel
    seed: Optional[bytes]
    params: Optional[DomainParameters]
    privkey: Optional[int]
    pubkey: Optional[Point]

    def __init__(self, model: CurveModel, coords: CoordinateModel):
        self.model = model
        self.coords = coords
        self.seed = None
        self.params = None
        self.privkey = None
        self.pubkey = None

    def init_prng(self, seed: bytes) -> None:
        self.write(cmd_init_prng(seed).encode())
        self.read(1)
        self.seed = seed

    def set_params(self, params: DomainParameters) -> None:
        self.write(cmd_set_params(params).encode())
        self.read(1)
        self.params = params

    def generate(self) -> Tuple[int, Point]:
        self.write(cmd_generate().encode())
        priv = self.read(1).decode()[1:-1]
        pub = self.read(1).decode()[1:-1]
        self.read(1)
        self.privkey = int(priv, 16)
        pub_len = len(pub)
        x = int(pub[:pub_len // 2], 16)
        y = int(pub[pub_len // 2:], 16)
        self.pubkey = Point(AffineCoordinateModel(self.model), x=Mod(x, self.params.curve.prime),
                            y=Mod(y, self.params.curve.prime))
        return self.privkey, self.pubkey

    def set_privkey(self, privkey: int) -> None:
        self.write(cmd_set_privkey(privkey).encode())
        self.read(1)
        self.privkey = privkey

    def set_pubkey(self, pubkey: Point) -> None:
        self.write(cmd_set_pubkey(pubkey).encode())
        self.read(1)
        self.pubkey = pubkey

    def scalar_mult(self, scalar: int) -> Point:
        self.write(cmd_scalar_mult(scalar).encode())
        result = self.read(1)[1:-1]
        plen = ((self.params.curve.prime.bit_length() + 7) // 8) * 2
        self.read(1)
        params = {var: Mod(int(result[i * plen:(i + 1) * plen], 16), self.params.curve.prime) for
                  i, var in enumerate(self.coords.variables)}
        return Point(self.coords, **params)

    def ecdh(self, other_pubkey: Point) -> bytes:
        self.write(cmd_ecdh(other_pubkey).encode())
        result = self.read(1)
        self.read(1)
        return unhexlify(result[1:-1])

    def ecdsa_sign(self, data: bytes) -> bytes:
        self.write(cmd_ecdsa_sign(data).encode())
        signature = self.read(1)
        self.read(1)
        return unhexlify(signature[1:-1])

    def ecdsa_verify(self, data: bytes, signature: bytes) -> bool:
        self.write(cmd_ecdsa_verify(data, signature).encode())
        result = self.read(1)
        self.read(1)
        return unhexlify(result[1:-1])[0] == 1

    def debug(self) -> Tuple[str, str]:
        self.write(cmd_debug().encode())
        resp = self.read(1)
        self.read(1)
        model, coords = unhexlify(resp[1:-1]).decode().split(",")
        return model, coords


@public
class BinaryTarget(ImplTarget):
    binary: str
    process: Optional[Popen]
    debug_output: bool

    def __init__(self, binary: str, model: CurveModel, coords: CoordinateModel, debug_output: bool = False):
        super().__init__(model, coords)
        self.binary = binary
        self.debug_output = debug_output

    def connect(self):
        self.process = Popen([self.binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             text=True, bufsize=1)

    def write(self, data: bytes):
        if self.process is None:
            raise ValueError
        if self.debug_output:
            print(">>", data.decode())
        self.process.stdin.write(data.decode() + "\n")
        self.process.stdin.flush()

    def read(self, timeout: int) -> bytes:
        if self.process is None:
            raise ValueError
        read = self.process.stdout.readline().encode()
        if self.debug_output:
            print("<<", read.decode(), end="")
        return read

    def disconnect(self):
        if self.process is None:
            return
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.terminate()
        self.process.wait()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--platform", envvar="PLATFORM", required=True,
              type=click.Choice(Platform.names()),
              callback=wrap_enum(Platform),
              help="The target platform to use.")
@click.option("--binary", help="For HOST target only. The binary to run.")
@click.argument("model", required=True,
                type=click.Choice(["shortw", "montgom", "edwards", "twisted"]),
                callback=get_model)
@click.argument("coords", required=True,
                callback=get_coords)
@click.version_option()
@click.pass_context
@public
def main(ctx, platform, binary, model, coords):
    """
    A tool for communicating with built and flashed ECC implementations.
    """
    ctx.ensure_object(dict)
    if platform != Platform.HOST:
        from pyecsca.sca.target import has_chipwhisperer
        if not has_chipwhisperer:
            click.secho("ChipWhisperer not installed, targets require it.", fg="red", err=True)
            raise click.Abort
        from pyecsca.sca.target import SimpleSerialTarget
        import chipwhisperer as cw
        from chipwhisperer.capture.targets.simpleserial_readers.cwlite import \
            SimpleSerial_ChipWhispererLite
        ser = SimpleSerial_ChipWhispererLite()
        scope = cw.scope()
        scope.default_setup()
        ctx.obj["target"] = SimpleSerialTarget(ser, scope)
    else:
        if binary is None or not path.isfile(binary):
            click.secho("Binary is required if the target is the host.", fg="red", err=True)
            raise click.Abort
        ctx.obj["target"] = BinaryTarget(binary, model, coords)


def get_curve(ctx: click.Context, param, value: Optional[str]) -> DomainParameters:
    if value is None:
        return None
    ctx.ensure_object(dict)
    category, name = value.split("/")
    curve = get_params(category, name, ctx.obj["coords"].name)
    return curve


@main.command("gen")
@click.argument("curve", required=True, callback=get_curve)
@click.pass_context
@public
def generate(ctx: click.Context, curve):
    ctx.ensure_object(dict)
    target: ImplTarget = ctx.obj["target"]
    target.connect()
    target.set_params(curve)
    click.echo(target.generate())
    target.disconnect()


@main.command("ecdh")
@click.pass_context
@public
def ecdh(ctx: click.Context):
    ctx.ensure_object(dict)


@main.command("ecdsa")
@click.pass_context
@public
def ecdsa(ctx: click.Context):
    ctx.ensure_object(dict)


if __name__ == "__main__":
    main(obj={})
