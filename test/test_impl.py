from copy import copy
from os.path import join
import pytest
from click.testing import CliRunner

from pyecsca.ec.key_agreement import ECDH_SHA1
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import (
    LTRMultiplier,
    RTLMultiplier,
    CoronMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    SlidingWindowMultiplier,
    AccumulationOrder,
    ProcessingDirection,
    ScalarMultiplier,
    FixedWindowLTRMultiplier,
)
from pyecsca.ec.signature import ECDSA_SHA1, SignatureResult

from pyecsca.codegen.builder import build_impl
from pyecsca.codegen.client import HostTarget, ImplTarget


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(("--mul", "KARATSUBA", "--sqr", "KARATSUBA"), id="Karatsuba"),
        pytest.param(("--mul", "TOOM_COOK", "--sqr", "TOOM_COOK"), id="ToomCook"),
        pytest.param(("--red", "BARRETT"), id="Barrett"),
        pytest.param(("--red", "MONTGOMERY"), id="Montgomery"),
    ],
)
def additional(request):
    return request.param


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(
            (
                LTRMultiplier,
                "ltr",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"complete": False},
            ),
            id="LTR1",
        ),
        pytest.param(
            (
                LTRMultiplier,
                "ltr",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"complete": True},
            ),
            id="LTR2",
        ),
        pytest.param(
            (
                LTRMultiplier,
                "ltr",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"complete": False, "always": True},
            ),
            id="LTR3",
        ),
        pytest.param(
            (
                LTRMultiplier,
                "ltr",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"complete": True, "always": True},
            ),
            id="LTR4",
        ),
        pytest.param(
            (
                LTRMultiplier,
                "ltr",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"complete": False, "accumulation_order": AccumulationOrder.PeqRP},
            ),
            id="LTR5",
        ),
        pytest.param(
            (RTLMultiplier, "rtl", ["add-1998-cmo", "dbl-1998-cmo"], {"always": False}),
            id="RTL1",
        ),
        pytest.param(
            (RTLMultiplier, "rtl", ["add-1998-cmo", "dbl-1998-cmo"], {"always": True}),
            id="RTL2",
        ),
        pytest.param(
            (CoronMultiplier, "coron", ["add-1998-cmo", "dbl-1998-cmo"], {}), id="Coron"
        ),
        pytest.param(
            (
                BinaryNAFMultiplier,
                "bnaf",
                ["add-1998-cmo", "dbl-1998-cmo", "neg"],
                {"direction": ProcessingDirection.LTR},
            ),
            id="BNAF1",
        ),
        pytest.param(
            (
                BinaryNAFMultiplier,
                "bnaf",
                ["add-1998-cmo", "dbl-1998-cmo", "neg"],
                {"direction": ProcessingDirection.RTL},
            ),
            id="BNAF2",
        ),
        pytest.param(
            (
                WindowNAFMultiplier,
                "wnaf",
                ["add-1998-cmo", "dbl-1998-cmo", "neg"],
                {"width": 3},
            ),
            id="WNAF1",
        ),
        pytest.param(
            (
                WindowNAFMultiplier,
                "wnaf",
                ["add-1998-cmo", "dbl-1998-cmo", "neg"],
                {"width": 3, "precompute_negation": True},
            ),
            id="WNAF2",
        ),
        pytest.param(
            (
                SlidingWindowMultiplier,
                "sliding",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"width": 3},
            ),
            id="SLI1",
        ),
        pytest.param(
            (
                SlidingWindowMultiplier,
                "sliding",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"width": 3, "recoding_direction": ProcessingDirection.RTL},
            ),
            id="SLI2",
        ),
        pytest.param(
            (
                FixedWindowLTRMultiplier,
                "fixed",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"m": 4},
            ),
            id="FIX1",
        ),
        pytest.param(
            (
                FixedWindowLTRMultiplier,
                "fixed",
                ["add-1998-cmo", "dbl-1998-cmo"],
                {"m": 5},
            ),
            id="FIX2",
        ),
    ],
)
def target(request, additional, secp128r1) -> ImplTarget:
    mult_class, mult_name, formulas, mult_kwargs = request.param
    runner = CliRunner()
    with runner.isolated_filesystem() as tmpdir:
        res = runner.invoke(
            build_impl,
            [
                "--platform",
                "HOST",
                *additional,
                "--ecdsa",
                "--ecdh",
                secp128r1.curve.model.shortname,
                secp128r1.curve.coordinate_model.name,
                *formulas,
                f"{mult_name}({','.join(f'{key}={value}' for key, value in mult_kwargs.items())})",
                ".",
            ],
            env={
                "CFLAGS": "-fsanitize=address -fsanitize=undefined -fno-sanitize-recover=all"
            }
        )
        assert res.exit_code == 0
        target = HostTarget(
            secp128r1.curve.model,
            secp128r1.curve.coordinate_model,
            binary=join(tmpdir, "pyecsca-codegen-HOST.elf"),
        )
        formula_instances = [
            secp128r1.curve.coordinate_model.formulas[formula] for formula in formulas
        ]
        mult = mult_class(*formula_instances, **mult_kwargs)
        target.mult = mult
        yield target


@pytest.fixture(scope="module")
def mult(target) -> ScalarMultiplier:
    return target.mult  # noqa


def test_init(target):
    target.connect()
    target.init_prng(bytes([0x12, 0x34, 0x56, 0x78]))
    target.disconnect()


def test_setup(target, mult, secp128r1):
    priv = 57
    mult.init(secp128r1, secp128r1.generator)
    pub = mult.multiply(priv).to_affine()
    target.connect()
    target.set_privkey(priv)
    target.set_pubkey(pub)
    target.disconnect()


def test_debug(target, secp128r1):
    target.connect()
    model, coords = target.debug()
    assert model == secp128r1.curve.model.shortname
    assert coords == secp128r1.curve.coordinate_model.name
    target.disconnect()


def test_keygen(target, mult, secp128r1):
    target.connect()
    target.set_params(secp128r1)
    mult.init(secp128r1, secp128r1.generator)
    for _ in range(10):
        priv, pub = target.generate()
        assert secp128r1.curve.is_on_curve(pub)
        expected = mult.multiply(priv).to_affine()
        assert pub == expected
    target.disconnect()


def test_scalarmult(target, mult, secp128r1):
    target.connect()
    target.set_params(secp128r1)
    mult.init(secp128r1, secp128r1.generator)
    values = [15, 2355498743, 3253857901321912443757746]
    for value in values:
        result = target.scalar_mult(value, target.params.generator)
        expected = mult.multiply(value)
        assert result == expected
    target.disconnect()


def test_ecdh(target, mult, secp128r1):
    target.connect()
    target.set_params(secp128r1)
    mult.init(secp128r1, secp128r1.generator)
    other_privs = [15, 2355498743, 3253857901321912443757746]
    for other_priv in other_privs:
        priv, pub = target.generate()
        other_pub = mult.multiply(other_priv)
        ecdh = ECDH_SHA1(copy(mult), secp128r1, other_pub, Mod(priv, secp128r1.order))
        result = target.ecdh(other_pub)
        expected = ecdh.perform()
        assert result == expected
    target.disconnect()


def test_ecdsa(target, mult, secp128r1):
    target.connect()
    target.set_params(secp128r1)
    mult.init(secp128r1, secp128r1.generator)

    messages = [b"something", b"something quite a bit longer than the hash thing"]
    for message in messages:
        priv, pub = target.generate()
        ecdsa = ECDSA_SHA1(
            copy(mult),
            secp128r1,
            mult.formulas["add"],
            pub.to_model(secp128r1.curve.coordinate_model, secp128r1.curve),
            Mod(priv, secp128r1.order),
        )

        signature_data = target.ecdsa_sign(message)
        result = SignatureResult.from_DER(signature_data)
        assert ecdsa.verify_data(result, message)

        expected = ecdsa.sign_data(message).to_DER()
        assert target.ecdsa_verify(message, expected)
    target.disconnect()
