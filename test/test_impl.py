from binascii import hexlify
from copy import copy
from os.path import join
from unittest import TestCase

from click.testing import CliRunner
from pyecsca.ec.curves import get_params
from pyecsca.ec.key_agreement import ECDH_SHA1
from pyecsca.ec.mult import LTRMultiplier, RTLMultiplier, CoronMultiplier, BinaryNAFMultiplier
from pyecsca.ec.point import Point
from pyecsca.ec.signature import ECDSA_SHA1, SignatureResult

from pyecsca.codegen.builder import build_impl
from pyecsca.codegen.client import HostTarget


class ImplTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model

        self.curve25519 = get_params("other", "Curve25519", "xz")
        self.base25519 = self.curve25519.generator
        self.coords25519 = self.curve25519.curve.coordinate_model

    def do_basic_test(self, callback, runner, params, mult_class, formulas, mult_name,
                      ecdsa, ecdh, **mult_kwargs):
        with runner.isolated_filesystem() as tmpdir:
            runner.invoke(build_impl,
                          ["--platform", "HOST",
                           "--ecdsa" if ecdsa else "--no-ecdsa",
                           "--ecdh" if ecdh else "--no-ecdh",
                           params.curve.model.shortname, params.curve.coordinate_model.name,
                           *formulas,
                           f"{mult_name}({','.join(f'{key}={value}' for key, value in mult_kwargs.items())})",
                           "."])
            target = HostTarget(params.curve.model, params.curve.coordinate_model,
                                binary=join(tmpdir, "pyecsca-codegen-HOST.elf"))
            target.connect()
            target.set_params(params)
            formula_instances = [params.curve.coordinate_model.formulas[formula] for formula
                                 in formulas]
            mult = mult_class(*formula_instances, **mult_kwargs)
            mult.init(params, params.generator)
            callback(target, mult, params)
            target.disconnect()


class PRNGTests(ImplTests):

    def test_init(self):
        runner = CliRunner()

        def callback(target, mult, params):
            target.init_prng(bytes([0x12, 0x34, 0x56, 0x78]))

        self.do_basic_test(callback, runner, self.secp128r1, LTRMultiplier,
                           ["add-1998-cmo", "dbl-1998-cmo"], "ltr", False, False, complete=False)


class SetupTests(ImplTests):

    def test_setup(self):
        runner = CliRunner()

        def callback(target, mult, params):
            priv = 57
            pub = mult.multiply(priv).to_affine()
            target.set_privkey(priv)
            target.set_pubkey(pub)

        self.do_basic_test(callback, runner, self.secp128r1, LTRMultiplier,
                           ["add-1998-cmo", "dbl-1998-cmo"], "ltr", False, False, complete=False)

    def test_debug(self):
        runner = CliRunner()
        def callback(target, mult, params):
            model, coords = target.debug()
            self.assertEqual(model, params.curve.model.shortname)
            self.assertEqual(coords, params.curve.coordinate_model.name)
        self.do_basic_test(callback, runner, self.secp128r1, LTRMultiplier,
                           ["add-1998-cmo", "dbl-1998-cmo"], "ltr", False, False, complete=False)

class KeyGenerationTests(ImplTests):

    def do_keygen_test(self, runner, params, mult_class, formulas, mult_name, **mult_kwargs):
        def callback(target, mult, params):
            for _ in range(10):
                priv, pub = target.generate()
                self.assertTrue(params.curve.is_on_curve(pub))
                expected = mult.multiply(priv).to_affine()
                self.assertEqual(pub, expected)

        self.do_basic_test(callback, runner, params, mult_class, formulas, mult_name, False, False,
                           **mult_kwargs)

    def test_ltr(self):
        runner = CliRunner()
        self.do_keygen_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                            "ltr", complete=False)
        self.do_keygen_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                            "ltr", complete=True)
        self.do_keygen_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                            "ltr", always=True, complete=False)
        self.do_keygen_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                            "ltr", always=True, complete=True)

    def test_rtl(self):
        runner = CliRunner()
        self.do_keygen_test(runner, self.secp128r1, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                            "rtl", always=False)
        self.do_keygen_test(runner, self.secp128r1, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                            "rtl", always=True)

    def test_coron(self):
        runner = CliRunner()
        self.do_keygen_test(runner, self.secp128r1, CoronMultiplier,
                            ["add-1998-cmo", "dbl-1998-cmo"], "coron")

    def test_bnaf(self):
        runner = CliRunner()
        self.do_keygen_test(runner, self.secp128r1, BinaryNAFMultiplier,
                            ["add-1998-cmo", "dbl-1998-cmo", "neg"], "bnaf")

    # def test_ladder(self):
    #    runner = CliRunner()
    #    self.do_keygen_test(runner, self.curve25519, LadderMultiplier, ["ladd-1987-m", "dbl-1987-m"], "ldr")
    #    # TODO: what about coords where generator is not affine?


class ScalarMultiplicationTests(ImplTests):

    def do_mult_test(self, runner, params, mult_class, formulas, mult_name, **mult_kwargs):
        values = [15, 2355498743, 3253857901321912443757746]

        def callback(target, mult, params):
            for value in values:
                result = target.scalar_mult(value)
                expected = mult.multiply(value)
                self.assertEqual(result, expected)

        self.do_basic_test(callback, runner, params, mult_class, formulas, mult_name, False, False,
                           **mult_kwargs)

    def test_ltr(self):
        runner = CliRunner()
        self.do_mult_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr", complete=False)
        self.do_mult_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr", complete=True)
        self.do_mult_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr", complete=False, always=True)
        self.do_mult_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr", complete=True, always=True)

    def test_rtl(self):
        runner = CliRunner()
        self.do_mult_test(runner, self.secp128r1, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "rtl", always=False)
        self.do_mult_test(runner, self.secp128r1, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "rtl", always=True)

    def test_coron(self):
        runner = CliRunner()
        self.do_mult_test(runner, self.secp128r1, CoronMultiplier,
                          ["add-1998-cmo", "dbl-1998-cmo"], "coron")

    def test_bnaf(self):
        runner = CliRunner()
        self.do_mult_test(runner, self.secp128r1, BinaryNAFMultiplier,
                          ["add-1998-cmo", "dbl-1998-cmo", "neg"], "bnaf")


class ECDHTests(ImplTests):
    def do_ecdh_test(self, runner, params, mult_class, formulas, mult_name, **mult_kwargs):
        other_privs = [15, 2355498743, 3253857901321912443757746]

        def callback(target, mult, params):
            for other_priv in other_privs:
                priv, pub = target.generate()
                other_pub = mult.multiply(other_priv)
                ecdh = ECDH_SHA1(copy(mult), params, other_pub, priv)
                result = target.ecdh(other_pub)
                expected = ecdh.perform()
                self.assertEqual(result, expected)

        self.do_basic_test(callback, runner, params, mult_class, formulas, mult_name, False, True,
                           **mult_kwargs)

    def test_ltr(self):
        runner = CliRunner()
        self.do_ecdh_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr", complete=False)
        self.do_ecdh_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr", complete=True)
        self.do_ecdh_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr", complete=False, always=True)
        self.do_ecdh_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "ltr", complete=True, always=True)

    def test_rtl(self):
        runner = CliRunner()
        self.do_ecdh_test(runner, self.secp128r1, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "rtl", always=False)
        self.do_ecdh_test(runner, self.secp128r1, RTLMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                          "rtl", always=True)

    def test_coron(self):
        runner = CliRunner()
        self.do_ecdh_test(runner, self.secp128r1, CoronMultiplier,
                          ["add-1998-cmo", "dbl-1998-cmo"], "coron")

    def test_bnaf(self):
        runner = CliRunner()
        self.do_ecdh_test(runner, self.secp128r1, BinaryNAFMultiplier,
                          ["add-1998-cmo", "dbl-1998-cmo", "neg"], "bnaf")


class ECDSATests(ImplTests):
    def do_ecdsa_test(self, runner, params, mult_class, formulas, mult_name, **mult_kwargs):
        data = b"something"

        def callback(target, mult, params):
            priv, pub = target.generate()
            ecdsa = ECDSA_SHA1(copy(mult), params, mult.formulas["add"],
                               Point.from_affine(params.curve.coordinate_model, pub), priv)


            signature_data = target.ecdsa_sign(data)
            result = SignatureResult.from_DER(signature_data)
            self.assertTrue(ecdsa.verify_data(result, data))

            expected = ecdsa.sign_data(data).to_DER()
            self.assertTrue(target.ecdsa_verify(data, expected))

        self.do_basic_test(callback, runner, params, mult_class, formulas, mult_name, True,
                           False, **mult_kwargs)

    def test_ltr(self):
        runner = CliRunner()
        self.do_ecdsa_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "ltr", complete=False)
        self.do_ecdsa_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "ltr", complete=True)
        self.do_ecdsa_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "ltr", complete=False, always=True)
        self.do_ecdsa_test(runner, self.secp128r1, LTRMultiplier, ["add-1998-cmo", "dbl-1998-cmo"],
                           "ltr", complete=True, always=True)
