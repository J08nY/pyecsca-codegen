import pytest

from pyecsca.codegen.builder import build_impl, list_impl


@pytest.mark.parametrize(
    "name,args",
    [
        (
            "basic",
            [
                "--platform",
                "HOST",
                "shortw",
                "projective",
                "add-1998-cmo",
                "dbl-1998-cmo",
                "z",
                "ltr(complete=True)",
                ".",
            ],
        ),
        (
            "karatsuba",
            [
                "--platform",
                "HOST",
                "--mul",
                "KARATSUBA",
                "shortw",
                "projective",
                "add-1998-cmo",
                "dbl-1998-cmo",
                "z",
                "ltr(complete=True)",
                ".",
            ],
        ),
        (
            "strip",
            [
                "--platform",
                "HOST",
                "--strip",
                "--no-remove",
                "shortw",
                "projective",
                "add-1998-cmo",
                "dbl-1998-cmo",
                "z",
                "ltr(complete=True)",
                ".",
            ],
        ),
        (
            "montgom",
            [
                "--platform",
                "HOST",
                "--no-ecdsa",
                "montgom",
                "xz",
                "ladd-1987-m",
                "dbl-1987-m",
                "scale",
                "ldr()",
                ".",
            ],
        ),
        (
            "jacobian",
            [
                "--platform",
                "HOST",
                "--no-ecdsa",
                "shortw",
                "jacobian",
                "add-2007-bl",
                "dbl-2007-bl",
                "rtl()",
                ".",
            ],
        ),
    ],
)
def test_cli_build(name, args, isolated_cli_runner):
    result = isolated_cli_runner.invoke(build_impl, args)
    assert result.exit_code == 0


def test_cli_build_fails(isolated_cli_runner):
    # unknown model
    result = isolated_cli_runner.invoke(
        build_impl,
        [
            "--platform",
            "HOST",
            "missing",
            "projective",
            "add-1998-cmo",
            "dbl-1998-cmo",
            "z",
            "ltr(complete=True)",
            ".",
        ],
    )
    assert result.exit_code == 2
    result = isolated_cli_runner.invoke(
        build_impl,
        [
            "--platform",
            "HOST",
            "shortw",
            "missing",
            "add-1998-cmo",
            "dbl-1998-cmo",
            "z",
            "ltr(complete=True)",
            ".",
        ],
    )
    assert result.exit_code == 2
    result = isolated_cli_runner.invoke(
        build_impl,
        [
            "--platform",
            "HOST",
            "shortw",
            "projective",
            "missing",
            "dbl-1998-cmo",
            "z",
            "ltr(complete=True)",
            ".",
        ],
    )
    assert result.exit_code == 2
    result = isolated_cli_runner.invoke(
        build_impl,
        [
            "--platform",
            "HOST",
            "shortw",
            "projective",
            "add-1998-cmo",
            "dbl-1998-cmo",
            "z",
            "missing",
            ".",
        ],
    )
    assert result.exit_code == 2
    result = isolated_cli_runner.invoke(
        build_impl,
        [
            "--platform",
            "HOST",
            "shortw",
            "projective",
            "add-1998-cmo",
            "dbl-1998-cmo",
            "z",
            "missing()",
            ".",
        ],
    )
    assert result.exit_code == 2
    result = isolated_cli_runner.invoke(
        build_impl,
        [
            "--platform",
            "HOST",
            "shortw",
            "projective",
            "add-1998-cmo",
            "z",
            "ltr(complete=True)",
            ".",
        ],
    )
    assert result.exit_code == 2
    result = isolated_cli_runner.invoke(
        build_impl,
        [
            "--platform",
            "HOST",
            "shortw",
            "projective",
            "add-1998-cmo",
            "add-1998-cmo",
            "z",
            "ltr(complete=True)",
            ".",
        ],
    )
    assert result.exit_code == 2


def test_cli_list(cli_runner):
    result = cli_runner.invoke(list_impl, [])
    assert result.exit_code == 0
    result = cli_runner.invoke(list_impl, ["montgom"])
    assert result.exit_code == 0
    result = cli_runner.invoke(list_impl, ["montgom", "xz"])
    assert result.exit_code == 0
    result = cli_runner.invoke(list_impl, ["montgom", "xz", "ladd-1987-m"])
    assert result.exit_code == 0
