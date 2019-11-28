#!/usr/bin/env python3
from binascii import hexlify
from typing import Mapping, Union, Optional

import click
from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.group import AbelianGroup
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
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


@click.command()
@click.version_option()
def main():
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
    curve = EllipticCurve(model, coords,
                          p,
                          {"a": 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc,
                           "b": 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b})
    affine_g = Point(AffineCoordinateModel(model),
                     x=Mod(0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296, p),
                     y=Mod(0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5, p))
    g = Point.from_affine(coords, affine_g)
    neutral = Point(coords, X=Mod(0, p), Y=Mod(1, p), Z=Mod(0, p))
    group = AbelianGroup(curve, g, neutral,
                         0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551, 0x1)
    print(cmd_set_curve(group))


if __name__ == "__main__":
    main()
