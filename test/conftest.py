import pytest

from pyecsca.ec.mult import *
from pyecsca.ec.params import get_params, DomainParameters


@pytest.fixture(scope="session")
def secp128r1() -> DomainParameters:
    return get_params("secg", "secp128r1", "projective")


@pytest.fixture(scope="session")
def curve25519() -> DomainParameters:
    return get_params("other", "Curve25519", "xz")


# fmt: off
window_mults = [
    (SlidingWindowMultiplier, dict(width=2, recoding_direction=ProcessingDirection.LTR)),
    (SlidingWindowMultiplier, dict(width=3, recoding_direction=ProcessingDirection.LTR)),
    (SlidingWindowMultiplier, dict(width=4, recoding_direction=ProcessingDirection.LTR)),
    (SlidingWindowMultiplier, dict(width=5, recoding_direction=ProcessingDirection.LTR)),
    (SlidingWindowMultiplier, dict(width=6, recoding_direction=ProcessingDirection.LTR)),
    (SlidingWindowMultiplier, dict(width=2, recoding_direction=ProcessingDirection.RTL)),
    (SlidingWindowMultiplier, dict(width=3, recoding_direction=ProcessingDirection.RTL)),
    (SlidingWindowMultiplier, dict(width=4, recoding_direction=ProcessingDirection.RTL)),
    (SlidingWindowMultiplier, dict(width=5, recoding_direction=ProcessingDirection.RTL)),
    (SlidingWindowMultiplier, dict(width=6, recoding_direction=ProcessingDirection.RTL)),
    (FixedWindowLTRMultiplier, dict(m=2**1)),
    (FixedWindowLTRMultiplier, dict(m=2**2)),
    (FixedWindowLTRMultiplier, dict(m=2**3)),
    (FixedWindowLTRMultiplier, dict(m=2**4)),
    (FixedWindowLTRMultiplier, dict(m=2**5)),
    (FixedWindowLTRMultiplier, dict(m=2**6)),
    (WindowBoothMultiplier, dict(width=2)),
    (WindowBoothMultiplier, dict(width=3)),
    (WindowBoothMultiplier, dict(width=4)),
    (WindowBoothMultiplier, dict(width=5)),
    (WindowBoothMultiplier, dict(width=6))
]
naf_mults = [
    (WindowNAFMultiplier, dict(width=2)),
    (WindowNAFMultiplier, dict(width=3)),
    (WindowNAFMultiplier, dict(width=4)),
    (WindowNAFMultiplier, dict(width=5)),
    (WindowNAFMultiplier, dict(width=6)),
    (BinaryNAFMultiplier, dict(always=False, direction=ProcessingDirection.LTR)),
    (BinaryNAFMultiplier, dict(always=False, direction=ProcessingDirection.RTL)),
    (BinaryNAFMultiplier, dict(always=True, direction=ProcessingDirection.LTR)),
    (BinaryNAFMultiplier, dict(always=True, direction=ProcessingDirection.RTL)),
    (BinaryNAFMultiplier, dict(complete=False, always=False, direction=ProcessingDirection.LTR)),
    (BinaryNAFMultiplier, dict(complete=False, always=False, direction=ProcessingDirection.RTL)),
    (BinaryNAFMultiplier, dict(complete=False, always=True, direction=ProcessingDirection.LTR)),
    (BinaryNAFMultiplier, dict(complete=False, always=True, direction=ProcessingDirection.RTL))
]
comb_mults = [
    (CombMultiplier, dict(width=2, always=True)),
    (CombMultiplier, dict(width=3, always=True)),
    (CombMultiplier, dict(width=4, always=True)),
    (CombMultiplier, dict(width=5, always=True)),
    (CombMultiplier, dict(width=6, always=True)),
    (CombMultiplier, dict(width=2, always=False)),
    (CombMultiplier, dict(width=3, always=False)),
    (CombMultiplier, dict(width=4, always=False)),
    (CombMultiplier, dict(width=5, always=False)),
    (CombMultiplier, dict(width=6, always=False)),
    (BGMWMultiplier, dict(width=2, direction=ProcessingDirection.LTR)),
    (BGMWMultiplier, dict(width=3, direction=ProcessingDirection.LTR)),
    (BGMWMultiplier, dict(width=4, direction=ProcessingDirection.LTR)),
    (BGMWMultiplier, dict(width=5, direction=ProcessingDirection.LTR)),
    (BGMWMultiplier, dict(width=6, direction=ProcessingDirection.LTR)),
    (BGMWMultiplier, dict(width=2, direction=ProcessingDirection.RTL)),
    (BGMWMultiplier, dict(width=3, direction=ProcessingDirection.RTL)),
    (BGMWMultiplier, dict(width=4, direction=ProcessingDirection.RTL)),
    (BGMWMultiplier, dict(width=5, direction=ProcessingDirection.RTL)),
    (BGMWMultiplier, dict(width=6, direction=ProcessingDirection.RTL))
]
binary_mults = [
    (LTRMultiplier, dict(always=False, complete=True)),
    (LTRMultiplier, dict(always=True,  complete=True)),
    (LTRMultiplier, dict(always=False, complete=False)),
    (LTRMultiplier, dict(always=True,  complete=False)),
    (RTLMultiplier, dict(always=False, complete=True)),
    (RTLMultiplier, dict(always=True,  complete=True)),
    (RTLMultiplier, dict(always=False, complete=False)),
    (RTLMultiplier, dict(always=True,  complete=False)),
    (CoronMultiplier, dict())
]
other_mults = [
    (FullPrecompMultiplier, dict(always=False, complete=True)),
    (FullPrecompMultiplier, dict(always=True,  complete=True)),
    (FullPrecompMultiplier, dict(always=False, complete=False)),
    (FullPrecompMultiplier, dict(always=True,  complete=False)),
    (SimpleLadderMultiplier, dict(complete=True)),
    (SimpleLadderMultiplier, dict(complete=False))
]
# fmt: on


@pytest.fixture(
    scope="session",
    params=window_mults + naf_mults + comb_mults + binary_mults + other_mults,
    ids=lambda p: "{}-{}".format(
        p[0].__name__, ":".join(f"{k}={v}" for k, v in p[1].items())
    ),
)
def simple_multiplier(request):
    return request.param
