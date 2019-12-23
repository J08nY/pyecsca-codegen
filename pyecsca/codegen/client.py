#!/usr/bin/env python3
from binascii import hexlify
from typing import Mapping, Union, Optional

import click
from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.group import AbelianGroup
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.point import Point


def encode_scalar(val: Union[int, Mod]) -> bytes:
    if isinstance(val, int):
        return val.to_bytes((val.bit_length() + 7) // 8, "big")
    elif isinstance(val, Mod):
        return encode_scalar(val.x)


def encode_point(point: Point) -> Mapping:
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
            result[chr(name | 0x7f)] = sub
            parsed += len(sub) + 2
        else:
            result[chr(name)] = data[parsed + 2: parsed + 2 + length]
            parsed += length + 2
    return result


def cmd_init_prng(seed: bytes) -> str:
    return "i" + hexlify(seed).decode()


def cmd_set_curve(group: AbelianGroup) -> str:
    data = {
        "p": encode_scalar(group.curve.prime),
        "n": encode_scalar(group.order),
        "h": encode_scalar(group.cofactor)
    }
    for param, value in group.curve.parameters.items():
        data[param] = encode_scalar(value)
    data["g"] = encode_point(group.generator)
    data["i"] = encode_point(group.neutral)
    return "c" + hexlify(encode_data(None, data)).decode()


def cmd_generate() -> str:
    return "g"


def cmd_set_privkey(privkey: int) -> str:
    return "s" + hexlify(encode_data(None, {"s": encode_scalar(privkey)})).decode()


def cmd_set_pubkey(pubkey: Point) -> str:
    return "w" + hexlify(encode_data(None, {"w": encode_point(pubkey)})).decode()


def cmd_scalar_mult(scalar: int) -> str:
    return "m" + hexlify(encode_data(None, {"s": encode_scalar(scalar)})).decode()


def cmd_ecdh(pubkey: Point) -> str:
    return "e" + hexlify(encode_data(None, {"w": encode_point(pubkey)})).decode()


def cmd_ecdsa_sign(data: bytes) -> str:
    return "a" + hexlify(encode_data(None, {"d": data})).decode()


def cmd_ecdsa_verify(data: bytes, sig: bytes) -> str:
    return "v" + hexlify(encode_data(None, {"d": data, "s": sig})).decode()


@click.command()
@click.version_option()
def main():
    pass
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


if __name__ == "__main__":
    main()
