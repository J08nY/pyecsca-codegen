from os.path import join
from unittest import TestCase

from click.testing import CliRunner
from pyecsca.ec.curves import get_params
from pyecsca.ec.mult import LTRMultiplier, RTLMultiplier, CoronMultiplier, BinaryNAFMultiplier

from pyecsca.codegen.builder import build_impl
from pyecsca.codegen.client import BinaryTarget


class KeyGenerationTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model

        self.curve25519 = get_params("other", "Curve25519", "xz")
        self.base25519 = self.curve25519.generator
        self.coords25519 = self.curve25519.curve.coordinate_model

    def do_basic_test(self, runner, params, mult_class, formulas, mult_name, **mult_kwargs):
        with runner.isolated_filesystem() as tmpdir:
            runner.invoke(build_impl,
                          ["--platform", "HOST", "--no-ecdsa", "--no-ecdh",
                           params.curve.model.shortname, params.curve.coordinate_model.name,
                           *formulas,
                           f"{mult_name}({','.join(f'{key}={value}' for key, value in mult_kwargs.items())})",
                           "."])
            target = BinaryTarget(join(tmpdir, "pyecsca-codegen-HOST.elf"),
                                  params.curve.model,
                                  params.curve.coordinate_model)
            target.connect()
            target.set_params(params)
            priv, pub = target.generate()
            self.assertTrue(params.curve.is_on_curve(pub))
            formula_instances = [params.curve.coordinate_model.formulas[formula] for formula
                                 in formulas]
            mult = mult_class(*formula_instances, **mult_kwargs)
            mult.init(params, params.generator)
            expected = mult.multiply(priv).to_affine()
            self.assertEqual(pub, expected)
            target.disconnect()

    def test_ltr(self):
        runner = CliRunner()
        self.do_basic_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "ltr",
                           complete=False)
        self.do_basic_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "ltr",
                           complete=True)
        self.do_basic_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "ltr",
                           always=True, complete=False)
        self.do_basic_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "ltr",
                           always=True, complete=True)

    def test_rtl(self):
        runner = CliRunner()
        self.do_basic_test(runner, self.secp128r1, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "rtl",
                           always=False)
        self.do_basic_test(runner, self.secp128r1, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "rtl",
                           always=True)

    def test_coron(self):
        runner = CliRunner()
        self.do_basic_test(runner, self.secp128r1, CoronMultiplier,
                           ["add-1998-cmo", "dbl-1998-cmo"], "coron")

    def test_bnaf(self):
        runner = CliRunner()
        self.do_basic_test(runner, self.secp128r1, BinaryNAFMultiplier,
                           ["add-1998-cmo", "dbl-1998-cmo", "neg"], "bnaf")

    # def test_ladder(self):
    #    runner = CliRunner()
    #    self.do_basic_test(runner, self.curve25519, LadderMultiplier, ["ladd-1987-m", "dbl-1987-m"], "ldr")
    #    # TODO: what about coords where generator is not affine?
