#!/usr/bin/env python3
import subprocess
from binascii import hexlify
from os import path
from subprocess import Popen
from typing import Mapping, Union, Optional

import click
from pyecsca.ec.curves import get_params
from pyecsca.ec.mod import Mod
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point, InfinityPoint
from pyecsca.sca import SerialTarget

from .common import wrap_enum, Platform, get_model, get_coords


def encode_scalar(val: Union[int, Mod]) -> bytes:
    if isinstance(val, int):
        return val.to_bytes((val.bit_length() + 7) // 8, "big")
    elif isinstance(val, Mod):
        return encode_scalar(int(val))


def encode_point(point: Point) -> Mapping:
    if isinstance(point, InfinityPoint):
        return {"n": bytes([1])}
    return {var: encode_scalar(value) for var, value in point.coords.items()}


def encode_data(name: Optional[str], structure: Union[Mapping, bytes]) -> bytes:
    if isinstance(structure, bytes):
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


def cmd_init_prng(seed: bytes) -> str:
    return "i" + hexlify(seed).decode()


def cmd_set_curve(group: DomainParameters) -> str:
    data = {
        "p": encode_scalar(group.curve.prime),
        "n": encode_scalar(group.order),
        "h": encode_scalar(group.cofactor)
    }
    for param, value in group.curve.parameters.items():
        data[param] = encode_scalar(value)
    data["g"] = encode_point(group.generator.to_affine())
    data["i"] = encode_point(group.neutral)
    return "c" + hexlify(encode_data(None, data)).decode()


def cmd_generate() -> str:
    return "g"


def cmd_set_privkey(privkey: int) -> str:
    return "s" + hexlify(encode_data(None, {"s": encode_scalar(privkey)})).decode()


def cmd_set_pubkey(pubkey: Point) -> str:
    return "w" + hexlify(encode_data(None, {"w": encode_point(pubkey.to_affine())})).decode()


def cmd_scalar_mult(scalar: int) -> str:
    return "m" + hexlify(encode_data(None, {"s": encode_scalar(scalar)})).decode()


def cmd_ecdh(pubkey: Point) -> str:
    return "e" + hexlify(encode_data(None, {"w": encode_point(pubkey.to_affine())})).decode()


def cmd_ecdsa_sign(data: bytes) -> str:
    return "a" + hexlify(encode_data(None, {"d": data})).decode()


def cmd_ecdsa_verify(data: bytes, sig: bytes) -> str:
    return "v" + hexlify(encode_data(None, {"d": data, "s": sig})).decode()


def cmd_debug() -> str:
    return "d"


class BinaryTarget(SerialTarget):
    binary: str
    process: Optional[Popen]

    def __init__(self, binary: str):
        self.binary = binary

    def connect(self):
        self.process = Popen([self.binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             text=True, bufsize=1)

    def write(self, data: bytes):
        self.process.stdin.write(data.decode() + "\n")
        self.process.stdin.flush()

    def read(self, timeout: int) -> bytes:
        return self.process.stdout.readline()

    def disconnect(self):
        if self.process.poll() is not None:
            self.process.terminate()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--platform", envvar="PLATFORM", required=True,
              type=click.Choice(Platform.names()),
              callback=wrap_enum(Platform),
              help="The target platform to use.")
@click.option("--binary", help="For HOST target only. The binary to run.")
@click.version_option()
@click.pass_context
def main(ctx, platform, binary):
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
        ctx.obj["target"] = BinaryTarget(binary)
    # model = ShortWeierstrassModel()
    # coords = model.coordinates["projective"]
    # p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
    # curve = EllipticCurve(model, coords,
    #                       p,
    #                       {"a": 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc,
    #                        "b": 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b})
    # affine_g = Point(AffineCoordinateModel(model),
    #                  x=Mod(0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296, p),
    #                  y=Mod(0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5, p))
    # g = Point.from_affine(coords, affine_g)
    # neutral = Point(coords, X=Mod(0, p), Y=Mod(1, p), Z=Mod(0, p))
    # group = AbelianGroup(curve, g, neutral,
    #                      0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551, 0x1)
    #
    # print(cmd_set_curve(group))
    # mul = LTRMultiplier(coords.formulas["add-1998-cmo"], coords.formulas["dbl-1998-cmo"], coords.formulas["z"])
    # mul.init(group, g)
    # res = mul.multiply(0x2EF035DF6D0634C7422161D08BCC794B5312E042DDB32B0135A4DE6E6345A555)
    # rx = Mod(0x77E3FF34C12571970845CBEB1BE0A79E3ECEE187510C2B8894BA800F8164C954, p)
    # ry = Mod(0x408A6A05607F9ACA97BB9A34EA643B107AADE0C9BB5EDB930EADE3009666B9D1, p)
    # rz = Mod(0xC66ECD687C335D63A7030434CA70351191BAFF1C206332EFEA39FA3003E91646, p)
    #
    # ox = Mod(0x3B1E7733E3250C97EB9D00AE0394F0768902DD337FEAAF7C4F6B9588462920DD, p)
    # oy = Mod(0xBA718497596C964E77F9666506505B1E730EE69D254E85AD44727DFFB2C7063E, p)
    # oz = Mod(0x0000000000000000000000000000000000000000000000000000000000000001, p)
    #
    # pt = Point(coords, X=rx, Y=ry, Z=rz)
    # ot = Point(coords, X=ox, Y=oy, Z=oz)
    # print(ot, res)
    # print(pt.equals(res))
    # print(ot.equals(res))
    # print(ot == res)


def get_curve(ctx: click.Context, param, value: Optional[str]) -> DomainParameters:
    if value is None:
        return None
    ctx.ensure_object(dict)
    category, name = value.split("/")
    curve = get_params(category, name, ctx.obj["coords"].name)
    return curve


@main.command("gen")
@click.argument("model", required=True,
                type=click.Choice(["shortw", "montgom", "edwards", "twisted"]),
                callback=get_model)
@click.argument("coords", required=True,
                callback=get_coords)
@click.argument("curve", required=True, callback=get_curve)
@click.pass_context
def generate(ctx: click.Context, model, coords, curve):
    ctx.ensure_object(dict)
    set_curve = cmd_set_curve(curve)
    generate = cmd_generate()
    target: SerialTarget = ctx.obj["target"]
    target.connect()
    click.echo(set_curve)
    target.write(set_curve.encode())
    click.echo(target.read(1))
    click.echo(generate)
    target.write(generate.encode())
    click.echo(target.read(1))
    click.echo(target.read(1))
    target.disconnect()


@main.command("ecdh")
@click.pass_context
def ecdh(ctx: click.Context):
    ctx.ensure_object(dict)


@main.command("ecdsa")
@click.pass_context
def ecdsa(ctx: click.Context):
    ctx.ensure_object(dict)


if __name__ == "__main__":
    main(obj={})
