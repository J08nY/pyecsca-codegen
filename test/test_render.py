import tempfile
from unittest import TestCase

from pyecsca.ec.configuration import HashType, RandomMod, Multiplication, Squaring, Reduction
from pyecsca.ec.curves import get_params
from pyecsca.ec.mult import LTRMultiplier

from pyecsca.codegen.common import Platform, DeviceConfiguration
from pyecsca.codegen.render import render_and_build


class RenderTests(TestCase):

    def test_basic_build(self):
        platform = Platform.HOST
        hash_type = HashType.SHA1
        mod_rand = RandomMod.REDUCE
        mult = Multiplication.BASE
        sqr = Squaring.BASE
        red = Reduction.BASE
        params = get_params("secg", "secp128r1", "projective")
        model = params.curve.model
        coords = params.curve.coordinate_model
        add = coords.formulas["add-1998-cmo"]
        dbl = coords.formulas["dbl-1998-cmo"]
        scl = coords.formulas["z"]
        formulas = [add, dbl, scl]
        scalarmult = LTRMultiplier(add, dbl, scl)
        config = DeviceConfiguration(model, coords, formulas, scalarmult, hash_type, mod_rand, mult,
                                     sqr, red, platform, True, True, True)
        temp = tempfile.mkdtemp()
        render_and_build(config, temp, True)
