from unittest import TestCase

from click.testing import CliRunner

from pyecsca.codegen.builder import build_impl, list_impl
from parameterized import parameterized

class BuilderTests(TestCase):

    @parameterized.expand([
        ("basic", ["--platform", "HOST", "shortw", "projective", "add-1998-cmo", "dbl-1998-cmo", "z", "ltr(complete=True)", "."]),
        ("karatsuba", ["--platform", "HOST", "--mul", "KARATSUBA", "shortw", "projective", "add-1998-cmo", "dbl-1998-cmo", "z", "ltr(complete=True)", "."]),
        ("strip", ["--platform", "HOST", "--strip", "--no-remove", "shortw", "projective", "add-1998-cmo", "dbl-1998-cmo", "z", "ltr(complete=True)", "."]),
        ("montgom", ["--platform", "HOST", "--no-ecdsa", "montgom", "xz", "ladd-1987-m", "dbl-1987-m", "scale", "ldr()", "."])
    ])
    def test_cli_build(self, name, args):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(build_impl, args)
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
