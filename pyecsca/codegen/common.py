from dataclasses import dataclass
from enum import Enum
from typing import List, Type
import click

from public import public
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.formula import Formula
from pyecsca.ec.model import CurveModel
from pyecsca.ec.mult import (ScalarMultiplier, LTRMultiplier, RTLMultiplier, CoronMultiplier,
                             LadderMultiplier, SimpleLadderMultiplier, DifferentialLadderMultiplier,
                             WindowNAFMultiplier, BinaryNAFMultiplier)


@public
class EnumDefine(Enum):
    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    @classmethod
    def names(cls):
        return list(e.name for e in cls)


@public
class Platform(EnumDefine):
    """Platform to build for."""
    HOST = "HOST"
    XMEGA = "CW308_XMEGA"
    STM32F0 = "CW308_STM32F0"
    STM32F3 = "CW308_STM32F3"


@public
class Multiplication(EnumDefine):
    """Base multiplication algorithm to use."""
    TOOM_COOK = "MUL_TOOM_COOK"
    KARATSUBA = "MUL_KARATSUBA"
    COMBA = "MUL_COMBA"
    BASE = "MUL_BASE"


@public
class Squaring(EnumDefine):
    """Base squaring algorithm to use."""
    TOOM_COOK = "SQR_TOOM_COOK"
    KARATSUBA = "SQR_KARATSUBA"
    COMBA = "SQR_COMBA"
    BASE = "SQR_BASE"


@public
class Reduction(EnumDefine):
    """Modular reduction method used."""
    BARRETT = "RED_BARRETT"
    MONTGOMERY = "RED_MONTGOMERY"
    BASE = "RED_BASE"


@public
class HashType(EnumDefine):
    """Hash algorithm used in ECDH and ECDSA."""
    NONE = "HASH_NONE"
    SHA1 = "HASH_SHA1"
    SHA224 = "HASH_SHA224"
    SHA256 = "HASH_SHA256"
    SHA384 = "HASH_SHA384"
    SHA512 = "HASH_SHA512"


@public
class RandomMod(EnumDefine):
    """Method of sampling a uniform integer modulo order."""
    SAMPLE = "MOD_RAND_SAMPLE"
    REDUCE = "MOD_RAND_REDUCE"


@public
@dataclass
class Configuration(object):
    platform: Platform
    hash_type: HashType
    mod_rand: RandomMod
    mult: Multiplication  # TODO: Use this
    sqr: Squaring  # TODO: Use this
    red: Reduction  # TODO: Use this
    model: CurveModel
    coords: CoordinateModel
    formulas: List[Formula]
    scalarmult: ScalarMultiplier
    keygen: bool
    ecdh: bool
    ecdsa: bool


MULTIPLIERS = [
    {
        "name": ("ltr", "LTRMultiplier"),
        "class": LTRMultiplier
    },
    {
        "name": ("rtl", "RTLMultiplier"),
        "class": RTLMultiplier
    },
    {
        "name": ("coron", "CoronMultiplier"),
        "class": CoronMultiplier
    },
    {
        "name": ("ldr", "LadderMultiplier"),
        "class": LadderMultiplier
    },
    {
        "name": ("simple-ldr", "SimpleLadderMultiplier"),
        "class": SimpleLadderMultiplier
    },
    {
        "name": ("diff-ldr", "DifferentialLadderMultiplier"),
        "class": DifferentialLadderMultiplier
    },
    {
        "name": ("naf", "bnaf", "BinaryNAFMultiplier"),
        "class": BinaryNAFMultiplier
    },
    {
        "name": ("wnaf", "WindowNAFMultiplier"),
        "class": WindowNAFMultiplier
    }
]


@public
def wrap_enum(enum_class: Type[EnumDefine]):
    def callback(ctx, param, value):
        try:
            res = getattr(enum_class, value)
            return res
        except Exception:
            raise click.BadParameter(
                    "Cannot create {} enum from {}.".format(enum_class.__name__, value))

    return callback
