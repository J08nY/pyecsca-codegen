from unittest import TestCase
import tempfile

from click.testing import CliRunner
from pyecsca.ec.curves import get_params
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.configuration import HashType, RandomMod, Multiplication, Squaring, Reduction

from pyecsca.codegen.common import Platform, DeviceConfiguration
from pyecsca.codegen.render import render_and_build
from pyecsca.codegen.builder import build_impl, list_impl


class BuilderTests(TestCase):

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

    def test_cli_build(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "-v", "shortw", "projective",
                                    "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "ltr(complete=True)", "."])
            self.assertEqual(result.exit_code, 0)
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "--strip", "--no-remove", "shortw",
                                    "projective",
                                    "add-1998-cmo", "dbl-1998-cmo", "z", "ltr(complete=True)",
                                    "."])
            self.assertEqual(result.exit_code, 0)
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "--no-ecdsa", "montgom",
                                    "xz", "ladd-1987-m", "dbl-1987-m", "scale", "ldr()",
                                    "."])
            self.assertEqual(result.exit_code, 0)

    def test_cli_build_fails(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            # unknown model
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "missing", "projective", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "ltr(complete=True)", "."])
            self.assertEqual(result.exit_code, 2)
            # unknown coordinates
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "missing", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "ltr(complete=True)", "."])
            self.assertEqual(result.exit_code, 2)
            # unknown formula
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "missing",
                                    "dbl-1998-cmo", "z", "ltr(complete=True)", "."])
            self.assertEqual(result.exit_code, 2)
            # bad formatted mult spec
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "missing", "."])
            self.assertEqual(result.exit_code, 2)
            # unknown mult
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "add-1998-cmo",
                                    "dbl-1998-cmo", "z", "missing()", "."])
            self.assertEqual(result.exit_code, 2)
            # missing required formulas to mult
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "add-1998-cmo",
                                    "z", "ltr(complete=True)", "."])
            self.assertEqual(result.exit_code, 2)
            # duplicate formulas
            result = runner.invoke(build_impl,
                                   ["--platform", "HOST", "shortw", "projective", "add-1998-cmo",
                                    "add-1998-cmo", "z", "ltr(complete=True)", "."])
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
