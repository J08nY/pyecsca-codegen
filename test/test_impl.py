from copy import copy
from os.path import join
import pytest

from pyecsca.ec.key_agreement import ECDH_SHA1
from pyecsca.ec.mult import (
    LTRMultiplier,
    RTLMultiplier,
    CoronMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    AccumulationOrder,
    ProcessingDirection,
)
from pyecsca.ec.signature import ECDSA_SHA1, SignatureResult

from pyecsca.codegen.builder import build_impl
from pyecsca.codegen.client import HostTarget


def do_basic_test(
    callback,
    runner,
    params,
    mult_class,
    formulas,
    mult_name,
    ecdsa,
    ecdh,
    **mult_kwargs,
):
    other_args = [
        ("--mul", "KARATSUBA", "--sqr", "KARATSUBA"),
        ("--mul", "TOOM_COOK", "--sqr", "TOOM_COOK"),
        ("--red", "BARRETT"),
        ("--red", "MONTGOMERY"),
    ]
    for additional in other_args:
        with runner.isolated_filesystem() as tmpdir:
            res = runner.invoke(
                build_impl,
                [
                    "--platform",
                    "HOST",
                    *additional,
                    "--ecdsa" if ecdsa else "--no-ecdsa",
                    "--ecdh" if ecdh else "--no-ecdh",
                    params.curve.model.shortname,
                    params.curve.coordinate_model.name,
                    *formulas,
                    f"{mult_name}({','.join(f'{key}={value}' for key, value in mult_kwargs.items())})",
                    ".",
                ],
            )
            assert res.exit_code == 0
            target = HostTarget(
                params.curve.model,
                params.curve.coordinate_model,
                binary=join(tmpdir, "pyecsca-codegen-HOST.elf"),
            )
            target.connect()
            target.set_params(params)
            formula_instances = [
                params.curve.coordinate_model.formulas[formula] for formula in formulas
            ]
            mult = mult_class(*formula_instances, **mult_kwargs)
            mult.init(params, params.generator)
            callback(target, mult, params)
            target.disconnect()


def test_init(cli_runner, secp128r1):
    def callback(target, mult, params):
        target.init_prng(bytes([0x12, 0x34, 0x56, 0x78]))

    do_basic_test(
        callback,
        cli_runner,
        secp128r1,
        LTRMultiplier,
        ["add-1998-cmo", "dbl-1998-cmo"],
        "ltr",
        False,
        False,
    )


def test_setup(cli_runner, secp128r1):
    def callback(target, mult, params):
        priv = 57
        pub = mult.multiply(priv).to_affine()
        target.set_privkey(priv)
        target.set_pubkey(pub)

    do_basic_test(
        callback,
        cli_runner,
        secp128r1,
        LTRMultiplier,
        ["add-1998-cmo", "dbl-1998-cmo"],
        "ltr",
        False,
        False,
    )


def test_debug(cli_runner, secp128r1):
    def callback(target, mult, params):
        model, coords = target.debug()
        assert model == params.curve.model.shortname
        assert coords == params.curve.coordinate_model.name

    do_basic_test(
        callback,
        cli_runner,
        secp128r1,
        LTRMultiplier,
        ["add-1998-cmo", "dbl-1998-cmo"],
        "ltr",
        False,
        False,
    )


MULTIPLIERS = [
    (LTRMultiplier, "ltr", ["add-1998-cmo", "dbl-1998-cmo"], {"complete": False}),
    (LTRMultiplier, "ltr", ["add-1998-cmo", "dbl-1998-cmo"], {"complete": True}),
    (
        LTRMultiplier,
        "ltr",
        ["add-1998-cmo", "dbl-1998-cmo"],
        {"complete": False, "always": True},
    ),
    (
        LTRMultiplier,
        "ltr",
        ["add-1998-cmo", "dbl-1998-cmo"],
        {"complete": True, "always": True},
    ),
    (
        LTRMultiplier,
        "ltr",
        ["add-1998-cmo", "dbl-1998-cmo"],
        {"complete": False, "accumulation_order": AccumulationOrder.PeqRP},
    ),
    (RTLMultiplier, "rtl", ["add-1998-cmo", "dbl-1998-cmo"], {"always": False}),
    (RTLMultiplier, "rtl", ["add-1998-cmo", "dbl-1998-cmo"], {"always": True}),
    (CoronMultiplier, "coron", ["add-1998-cmo", "dbl-1998-cmo"], {}),
    (BinaryNAFMultiplier, "bnaf", ["add-1998-cmo", "dbl-1998-cmo", "neg"], {"direction": ProcessingDirection.LTR}),
    (BinaryNAFMultiplier, "bnaf", ["add-1998-cmo", "dbl-1998-cmo", "neg"], {"direction": ProcessingDirection.RTL}),
    (WindowNAFMultiplier, "wnaf", ["add-1998-cmo", "dbl-1998-cmo", "neg"], {"width": 3}),
    (WindowNAFMultiplier, "wnaf", ["add-1998-cmo", "dbl-1998-cmo", "neg"], {"width": 3, "precompute_negation": True}),
]


@pytest.mark.parametrize("mult_class,mult_name,formulas,mult_kwargs", MULTIPLIERS)
def test_keygen(mult_class, mult_name, mult_kwargs, formulas, cli_runner, secp128r1):
    def callback(target, mult, params):
        for _ in range(10):
            priv, pub = target.generate()
            assert params.curve.is_on_curve(pub)
            expected = mult.multiply(priv).to_affine()
            assert pub == expected

    do_basic_test(
        callback,
        cli_runner,
        secp128r1,
        mult_class,
        formulas,
        mult_name,
        False,
        False,
        **mult_kwargs,
    )


@pytest.mark.parametrize("mult_class,mult_name,formulas,mult_kwargs", MULTIPLIERS)
def test_scalarmult(
    mult_class, mult_name, mult_kwargs, formulas, cli_runner, secp128r1
):
    values = [15, 2355498743, 3253857901321912443757746]

    def callback(target, mult, params):
        for value in values:
            result = target.scalar_mult(value, params.generator)
            expected = mult.multiply(value)
            assert result == expected

    do_basic_test(
        callback,
        cli_runner,
        secp128r1,
        mult_class,
        formulas,
        mult_name,
        False,
        False,
        **mult_kwargs,
    )


@pytest.mark.parametrize("mult_class,mult_name,formulas,mult_kwargs", MULTIPLIERS)
def test_ecdh(mult_class, mult_name, mult_kwargs, formulas, cli_runner, secp128r1):
    other_privs = [15, 2355498743, 3253857901321912443757746]

    def callback(target, mult, params):
        for other_priv in other_privs:
            priv, pub = target.generate()
            other_pub = mult.multiply(other_priv)
            ecdh = ECDH_SHA1(copy(mult), params, other_pub, priv)
            result = target.ecdh(other_pub)
            expected = ecdh.perform()
            assert result == expected

    do_basic_test(
        callback,
        cli_runner,
        secp128r1,
        mult_class,
        formulas,
        mult_name,
        False,
        True,
        **mult_kwargs,
    )


@pytest.mark.parametrize("mult_class,mult_name,formulas,mult_kwargs", MULTIPLIERS)
def test_ecdsa(mult_class, mult_name, mult_kwargs, formulas, cli_runner, secp128r1):
    data = b"something"

    def callback(target, mult, params):
        priv, pub = target.generate()
        ecdsa = ECDSA_SHA1(
            copy(mult),
            params,
            mult.formulas["add"],
            pub.to_model(params.curve.coordinate_model, params.curve),
            priv,
        )

        signature_data = target.ecdsa_sign(data)
        result = SignatureResult.from_DER(signature_data)
        assert ecdsa.verify_data(result, data)

        expected = ecdsa.sign_data(data).to_DER()
        assert target.ecdsa_verify(data, expected)

    do_basic_test(
        callback,
        cli_runner,
        secp128r1,
        mult_class,
        formulas,
        mult_name,
        True,
        False,
        **mult_kwargs,
    )
