import pytest
from pyecsca.ec.configuration import (
    HashType,
    RandomMod,
    Multiplication,
    Squaring,
    Reduction,
    Inversion,
)
from pyecsca.ec.mult import LTRMultiplier

from pyecsca.codegen.common import Platform, DeviceConfiguration
from pyecsca.codegen.render import render_and_build


@pytest.mark.xfail(reason="Issue not resolved yet.")
def test_regress_5(secp128r1, tmp_path):
    platform = Platform.HOST
    hash_type = HashType.SHA1
    mod_rand = RandomMod.REDUCE
    mult = Multiplication.BASE
    sqr = Squaring.BASE
    red = Reduction.BASE
    inv = Inversion.GCD
    model = secp128r1.curve.model
    coords = secp128r1.curve.coordinate_model
    add = coords.formulas["add-2015-rcb"]
    dbl = coords.formulas["dbl-2015-rcb"]
    scl = coords.formulas["z"]
    formulas = [add, dbl, scl]
    scalarmult = LTRMultiplier(add, dbl, scl)
    config = DeviceConfiguration(
        model,
        coords,
        formulas,
        scalarmult,
        hash_type,
        mod_rand,
        mult,
        sqr,
        red,
        inv,
        platform,
        True,
        True,
        True,
    )
    dir, elf_file, hex_file, res = render_and_build(config, str(tmp_path), True)
    assert res.returncode == 0
