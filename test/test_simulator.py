from copy import copy
from os.path import join
from unittest import TestCase

from click.testing import CliRunner
from pyecsca.ec.key_agreement import ECDH_SHA1
from pyecsca.ec.mult import LTRMultiplier, RTLMultiplier, CoronMultiplier, BinaryNAFMultiplier
from pyecsca.ec.signature import ECDSA_SHA1, SignatureResult

from pyecsca.codegen.builder import build_impl
from pyecsca.codegen.client import SimulatorTarget

from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import InfinityPoint, Point


class SimulatorTest(TestCase):

    def setUp(self):
        model = ShortWeierstrassModel()
        coords = model.coordinates["projective"]
        p = 0xd7d1247f
        a = Mod(0xa4a44016, p)
        b = Mod(0x73f76716, p)
        n = 0xd7d2a475
        h = 1
        gx, gy, gz = Mod(0x54eed6d7, p), Mod(0x6f1e55ac, p), Mod(1, p)
        generator = Point(coords, X=gx, Y=gy, Z=gz)
        neutral = InfinityPoint(coords)

        curve = EllipticCurve(model, coords, p, neutral, {"a": a, "b": b})
        self.curve32 = DomainParameters(curve, generator, n, h)
        self.base = self.curve32.generator
        self.coords = self.curve32.curve.coordinate_model

    def do_basic_test(self, callback, runner, params, mult_class, formulas, mult_name,
                      ecdsa, ecdh):
        with runner.isolated_filesystem() as tmpdir:
            runner.invoke(build_impl,
                        ["--platform", "STM32F3",
                        "--ecdsa" if ecdsa else "--no-ecdsa",
                        "--ecdh" if ecdh else "--no-ecdh", 
                        params.curve.model.shortname, params.curve.coordinate_model.name,
                        *formulas,
                        f"{mult_name}()",
                        "."])
            target = SimulatorTarget(params.curve.model, params.curve.coordinate_model)
            target.connect(binary=join(tmpdir, "pyecsca-codegen-CW308_STM32F3.elf"))
            target.set_params(params)
            formula_instances = [params.curve.coordinate_model.formulas[formula] for formula
                                    in formulas]
            mult = mult_class(*formula_instances)
            mult.init(params, params.generator)
            callback(target, mult, params)
            target.disconnect()


class PRNGTests(SimulatorTest):

    def test_init(self):
        runner = CliRunner()

        def callback(target, mult, params):
            target.init_prng(bytes([0x12, 0x34, 0x56, 0x78]))

        self.do_basic_test(callback, runner, self.curve32, LTRMultiplier,
                           ["add-1998-cmo", "dbl-1998-cmo"], "ltr", False, False)


class SetupTests(SimulatorTest):

    def test_setup(self):
        runner = CliRunner()

        def callback(target, mult, params):
            priv = 57
            pub = mult.multiply(priv).to_affine()
            target.set_privkey(priv)
            target.set_pubkey(pub)

        self.do_basic_test(callback, runner, self.curve32, LTRMultiplier,
                           ["add-1998-cmo", "dbl-1998-cmo"], "ltr", False, False)

    def test_debug(self):
        runner = CliRunner()

        def callback(target, mult, params):
            model, coords = target.debug()
            self.assertEqual(model, params.curve.model.shortname)
            self.assertEqual(coords, params.curve.coordinate_model.name)

        self.do_basic_test(callback, runner, self.curve32, LTRMultiplier,
                           ["add-1998-cmo", "dbl-1998-cmo"], "ltr", False, False)


class KeyGenerationTests(SimulatorTest):

    def do_keygen_test(self, runner, params, mult_class, formulas, mult_name):
        def callback(target, mult, params):
            priv, pub = target.generate()
            self.assertTrue(params.curve.is_on_curve(pub))
            expected = mult.multiply(priv).to_affine()
            self.assertEqual(pub, expected)

        self.do_basic_test(callback, runner, params, mult_class, formulas, mult_name, False, False)

    def test_ltr(self):
        runner = CliRunner()
        self.do_keygen_test(runner, self.curve32, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                            "ltr")

    def test_rtl(self):
        runner = CliRunner()
        self.do_keygen_test(runner, self.curve32, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                            "rtl")

    def test_coron(self):
        runner = CliRunner()
        self.do_keygen_test(runner, self.curve32, CoronMultiplier,
                            ["add-1998-cmo", "dbl-1998-cmo"], "coron")

    def test_bnaf(self):
        runner = CliRunner()
        self.do_keygen_test(runner, self.curve32, BinaryNAFMultiplier,
                            ["add-1998-cmo", "dbl-1998-cmo", "neg"], "bnaf")


class ScalarMultiplicationTests(SimulatorTest):

    def do_mult_test(self, runner, params, mult_class, formulas, mult_name):
        values = [2355498743]

        def callback(target, mult, params):
            for value in values:
                result = target.scalar_mult(value, params.generator)
                expected = mult.multiply(value)
                self.assertEqual(result, expected)

        self.do_basic_test(callback, runner, params, mult_class, formulas, mult_name, False, False)

    def test_ltr(self):
        runner = CliRunner()
        self.do_mult_test(runner, self.curve32, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr")

    def test_rtl(self):
        runner = CliRunner()
        self.do_mult_test(runner, self.curve32, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "rtl")

    def test_coron(self):
        runner = CliRunner()
        self.do_mult_test(runner, self.curve32, CoronMultiplier,
                          ["add-1998-cmo", "dbl-1998-cmo"], "coron")

    def test_bnaf(self):
        runner = CliRunner()
        self.do_mult_test(runner, self.curve32, BinaryNAFMultiplier,
                          ["add-1998-cmo", "dbl-1998-cmo", "neg"], "bnaf")


class ECDHTests(SimulatorTest):
    def do_ecdh_test(self, runner, params, mult_class, formulas, mult_name):
        other_privs = [2355498743]

        def callback(target, mult, params):
            for other_priv in other_privs:
                priv, pub = target.generate()
                other_pub = mult.multiply(other_priv)
                ecdh = ECDH_SHA1(copy(mult), params, other_pub, priv)
                result = target.ecdh(other_pub)
                expected = ecdh.perform()
                self.assertEqual(result, expected)

        self.do_basic_test(callback, runner, params, mult_class, formulas, mult_name, False, True)

    def test_ltr(self):
        runner = CliRunner()
        self.do_ecdh_test(runner, self.curve32, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr")

    def test_rtl(self):
        runner = CliRunner()
        self.do_ecdh_test(runner, self.curve32, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "rtl")

    def test_coron(self):
        runner = CliRunner()
        self.do_ecdh_test(runner, self.curve32, CoronMultiplier,
                          ["add-1998-cmo", "dbl-1998-cmo"], "coron")

    def test_bnaf(self):
        runner = CliRunner()
        self.do_ecdh_test(runner, self.curve32, BinaryNAFMultiplier,
                          ["add-1998-cmo", "dbl-1998-cmo", "neg"], "bnaf")


class ECDSATests(SimulatorTest):
    def do_ecdsa_test(self, runner, params, mult_class, formulas, mult_name):
        data = b"something"

        def callback(target, mult, params):
            priv, pub = target.generate()
            ecdsa = ECDSA_SHA1(copy(mult), params, mult.formulas["add"],
                               pub.to_model(params.curve.coordinate_model, params.curve), priv)

            signature_data = target.ecdsa_sign(data)
            result = SignatureResult.from_DER(bytes(signature_data))
            self.assertTrue(ecdsa.verify_data(result, data))

            expected = ecdsa.sign_data(data).to_DER()
            self.assertTrue(target.ecdsa_verify(data, expected))

        self.do_basic_test(callback, runner, params, mult_class, formulas, mult_name, True, False)

    def test_ltr(self):
        runner = CliRunner()
        self.do_ecdsa_test(runner, self.curve32, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"], "ltr")