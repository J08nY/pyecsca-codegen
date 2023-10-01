from dataclasses import dataclass
from typing import Type, Optional

import click
from public import public
from pyecsca.ec.configuration import EnumDefine, Configuration
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.model import (CurveModel, ShortWeierstrassModel, MontgomeryModel, EdwardsModel,
                              TwistedEdwardsModel)
from pyecsca.ec.mult import (
    LTRMultiplier,
    RTLMultiplier,
    CoronMultiplier,
    LadderMultiplier,
    SimpleLadderMultiplier,
    DifferentialLadderMultiplier,
    WindowNAFMultiplier,
    BinaryNAFMultiplier,
    SlidingWindowMultiplier,
)


@public
class Platform(EnumDefine):
    """Platform to build for."""
    HOST = "HOST"
    XMEGA = "CW308_XMEGA"
    STM32F0 = "CW308_STM32F0"
    STM32F3 = "CW308_STM32F3"
    NANO = "CWNANO"


@public
@dataclass(frozen=True)
class DeviceConfiguration(Configuration):
    """A device configuration that includes the platform and choices
    specific to the pyecsca-codegened implementations."""
    platform: Platform
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
    },
    {
        "name": ("sliding", "SlidingWindowMultiplier"),
        "class": SlidingWindowMultiplier
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


def get_model(ctx: click.Context, param, value: str) -> CurveModel:
    """A click callback func for model setup."""
    if value is None:
        return None
    classes = {
        "shortw": ShortWeierstrassModel,
        "montgom": MontgomeryModel,
        "edwards": EdwardsModel,
        "twisted": TwistedEdwardsModel
    }
    model = classes[value]()
    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    return model


def get_coords(ctx: click.Context, param, value: Optional[str]) -> Optional[CoordinateModel]:
    """A click callback func for coordinate setup."""
    if value is None:
        return None
    ctx.ensure_object(dict)
    model = ctx.obj["model"]
    if value not in model.coordinates:
        raise click.BadParameter(
                "Coordinate model '{}' is not a model in '{}'.".format(value,
                                                                       model.__class__.__name__))
    coords = model.coordinates[value]
    ctx.obj["coords"] = coords
    return coords
