from os.path import join
from unittest import TestCase

from click.testing import CliRunner
from pyecsca.ec.curves import get_params
from pyecsca.ec.mod import Mod

from pyecsca.codegen.builder import build_impl
from pyecsca.codegen.client import (encode_data, decode_data, encode_scalar, cmd_init_prng,
                                    cmd_set_params, cmd_set_pubkey, cmd_set_privkey,
                                    cmd_scalar_mult,
                                    cmd_ecdh, cmd_ecdsa_sign, cmd_ecdsa_verify, cmd_generate,
                                    cmd_debug, main)


class EncodingTests(TestCase):

    def test_encode_decode(self):
        data = {"a": encode_scalar(0xcafebabe),
                "b": {
                    "c": encode_scalar(Mod(1, 3)),
                    "d": bytes([0x2])
                }}
        encoded = encode_data(None, data)
        result = decode_data(encoded)
        self.assertEqual(data, result)


class CommandTest(TestCase):

    def setUp(self):
        self.curve = get_params("secg", "secp128r1", "projective")
        self.model = self.curve.curve.model
        self.coords = self.curve.curve.coordinate_model

    def test_init_prng(self):
        cmd_init_prng(bytes([0xca, 0xfe, 0xba, 0xbe]))

    def test_set_curve(self):
        cmd_set_params(self.curve)

    def test_generate(self):
        cmd_generate()

    def test_set_pubkey(self):
        cmd_set_pubkey(self.curve.generator)

    def test_set_privkey(self):
        cmd_set_privkey(0x123456789)

    def test_scalar_mult(self):
        cmd_scalar_mult(0x123456789)

    def test_ecdh(self):
        cmd_ecdh(self.curve.generator)

    def test_ecdsa_sign(self):
        cmd_ecdsa_sign(b"something")

    def test_ecdsa_verify(self):
        cmd_ecdsa_verify(b"something", b"signature")

    def test_debug(self):
        cmd_debug()


class ClientTests(TestCase):

    def test_generate(self):
        runner = CliRunner()
        with runner.isolated_filesystem() as tmpdir:
            runner.invoke(build_impl,
                          ["--platform", "HOST", "-v", "shortw", "projective",
                           "add-1998-cmo", "dbl-1998-cmo", "z", "ltr(complete=False)", "."])
            result = runner.invoke(main,
                                   ["--platform", "HOST", "--binary",
                                    join(tmpdir, "pyecsca-codegen-HOST.elf"),
                                    "shortw", "projective", "gen", "secg/secp128r1"])
            self.assertEqual(result.exit_code, 0)
