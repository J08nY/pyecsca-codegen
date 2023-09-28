from os.path import join

from pyecsca.codegen.builder import build_impl
from pyecsca.codegen.client import main


def test_generate(cli_runner):
    with cli_runner.isolated_filesystem() as tmpdir:
        cli_runner.invoke(
            build_impl,
            [
                "--platform",
                "HOST",
                "shortw",
                "projective",
                "add-1998-cmo",
                "dbl-1998-cmo",
                "z",
                "ltr(complete=False)",
                ".",
            ],
        )
        result = cli_runner.invoke(
            main,
            [
                "--platform",
                "HOST",
                "--fw",
                join(tmpdir, "pyecsca-codegen-HOST.elf"),
                "shortw",
                "projective",
                "gen",
                "secg/secp128r1",
            ],
        )
        assert result.exit_code == 0


def test_ecdh(cli_runner):
    with cli_runner.isolated_filesystem() as tmpdir:
        cli_runner.invoke(
            build_impl,
            [
                "--platform",
                "HOST",
                "shortw",
                "projective",
                "add-1998-cmo",
                "dbl-1998-cmo",
                "z",
                "ltr(complete=False)",
                ".",
            ],
        )
        result = cli_runner.invoke(
            main,
            [
                "--platform",
                "HOST",
                "--fw",
                join(tmpdir, "pyecsca-codegen-HOST.elf"),
                "shortw",
                "projective",
                "ecdh",
                "secg/secp128r1",
                "122835813094999453922649270086793500655,326514220558629293368386081113307347349",
            ],
        )
        assert result.exit_code == 0
        result = cli_runner.invoke(
            main,
            [
                "--platform",
                "HOST",
                "--fw",
                join(tmpdir, "pyecsca-codegen-HOST.elf"),
                "shortw",
                "projective",
                "ecdh",
                "secg/secp128r1",
                "045c69512b630addd5b6d347b7bce517eff5a459f98f015c6906ccfed3cf0bf995",
            ],
        )
        assert result.exit_code == 0
        result = cli_runner.invoke(
            main,
            [
                "--platform",
                "HOST",
                "--fw",
                join(tmpdir, "pyecsca-codegen-HOST.elf"),
                "shortw",
                "projective",
                "ecdh",
                "secg/secp128r1",
                "something",
            ],
        )
        assert result.exit_code == 2
