from unittest import TestCase
import tempfile

from click.testing import CliRunner
from pyecsca.ec.curves import get_curve
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.mod import Mod
from pyecsca.ec.point import Point

from pyecsca.codegen.common import *
from pyecsca.codegen.builder import *


class BuilderTests(TestCase):

    def test_basic_build(self):
        platform = Platform.HOST
        hash_type = HashType.SHA1
        mod_rand = RandomMod.REDUCE
        mult = Multiplication.BASE
        sqr = Squaring.BASE
        red = Reduction.BASE
        group = get_curve("secp128r1", "projective")
        model = group.curve.model
        coords = group.curve.coordinate_model
        group.neutral = Point(coords, X=Mod(0, group.curve.prime), Y=Mod(1, group.curve.prime),
                              Z=Mod(0, group.curve.prime))
        add = coords.formulas["add-1998-cmo"]
        dbl = coords.formulas["dbl-1998-cmo"]
        scl = coords.formulas["z"]
        formulas = [add, dbl, scl]
        scalarmult = LTRMultiplier(add, dbl, scl)
        config = Configuration(platform, hash_type, mod_rand, mult, sqr, red, model, coords,
                               formulas, scalarmult, True, True, True)
        temp = tempfile.mkdtemp()
        render_and_build(config, temp, True)

    def test_cli_build(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "-v", "shortw", "projective", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "ltr(complete=True)", "test.elf"])
            self.assertEqual(result.exit_code, 0)
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "--strip", "--no-remove", "shortw", "projective",
                                    "add-1998-cmo", "dbl-1998-cmo", "z", "ltr(complete=True)",
                                    "test_stripped.elf"])
            self.assertEqual(result.exit_code, 0)
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "--no-ecdsa", "montgom",
                                    "xz", "ladd-1987-m", "dbl-1987-m", "scale", "ldr()",
                                    "test_ldr.elf"])
            self.assertEqual(result.exit_code, 0)

    def test_cli_build_fails(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            # unknown model
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "missing", "projective", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "ltr(complete=True)", "test.elf"])
            self.assertEqual(result.exit_code, 2)
            # unknown coordinates
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "missing", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "ltr(complete=True)", "test.elf"])
            self.assertEqual(result.exit_code, 2)
            # unknown formula
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "missing",
                                    "dbl-1998-cmo", "z", "ltr(complete=True)", "test.elf"])
            self.assertEqual(result.exit_code, 2)
            # bad formatted mult spec
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "missing", "test.elf"])
            self.assertEqual(result.exit_code, 2)
            # unknown mult
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "missing()", "test.elf"])
            self.assertEqual(result.exit_code, 2)
            # missing required formulas to mult
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "add-1998-cmo",
                                    "z", "missing", "test.elf"])
            self.assertEqual(result.exit_code, 2)

    def test_cli_list(self):
        runner = CliRunner()
        result = runner.invoke(list_impl, [])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(list_impl, ["montgom"])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(list_impl, ["montgom", "xz"])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(list_impl, ["montgom", "xz", "ladd-1987-m"])
        self.assertEqual(result.exit_code, 0)
