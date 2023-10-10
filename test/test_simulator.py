from copy import copy
from os.path import join
import pytest

from pyecsca.ec.key_agreement import ECDH_SHA1
from pyecsca.ec.mult import LTRMultiplier, RTLMultiplier
from pyecsca.ec.signature import ECDSA_SHA1, SignatureResult
from rainbow import TraceConfig, HammingWeight

from pyecsca.codegen.builder import build_impl
from pyecsca.codegen.client import SimulatorTarget

from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import InfinityPoint, Point
import gc


@pytest.fixture(scope="module")
def curve32():
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    p = 0xD7D1247F
    a = Mod(0xA4A44016, p)
    b = Mod(0x73F76716, p)
    n = 0xD7D2A475
    h = 1
    gx, gy, gz = Mod(0x54EED6D7, p), Mod(0x6F1E55AC, p), Mod(1, p)
    generator = Point(coords, X=gx, Y=gy, Z=gz)
    neutral = InfinityPoint(coords)

    curve = EllipticCurve(model, coords, p, neutral, {"a": a, "b": b})
    params = DomainParameters(curve, generator, n, h)
    return params


def do_basic_test(
    callback, runner, params, mult_class, formulas, mult_name, ecdsa, ecdh
):
    with runner.isolated_filesystem() as tmpdir:
        runner.invoke(
            build_impl,
            [
                "--platform",
                "STM32F3",
                "--ecdsa" if ecdsa else "--no-ecdsa",
                "--ecdh" if ecdh else "--no-ecdh",
                "--red",
                "MONTGOMERY",
                "-D",
                "BN_NON_CONST",
                params.curve.model.shortname,
                params.curve.coordinate_model.name,
                *formulas,
                f"{mult_name}()",
                ".",
            ],
        )
        target = SimulatorTarget(params.curve.model, params.curve.coordinate_model)
        target.connect(binary=join(tmpdir, "pyecsca-codegen-CW308_STM32F3.elf"))
        target.set_params(params)
        formula_instances = [
            params.curve.coordinate_model.formulas[formula] for formula in formulas
        ]
        mult = mult_class(*formula_instances)
        mult.init(params, params.generator)
        callback(target, mult, params)
        target.disconnect()
        del target
        gc.collect()


def test_init(cli_runner, curve32):
    def callback(target, mult, params):
        target.init_prng(bytes([0x12, 0x34, 0x56, 0x78]))

    do_basic_test(
        callback,
        cli_runner,
        curve32,
        LTRMultiplier,
        ["add-1998-cmo", "dbl-1998-cmo"],
        "ltr",
        False,
        False,
    )


def test_setup(cli_runner, curve32):
    def callback(target, mult, params):
        priv = 57
        pub = mult.multiply(priv).to_affine()
        target.set_privkey(priv)
        target.set_pubkey(pub)

    do_basic_test(
        callback,
        cli_runner,
        curve32,
        LTRMultiplier,
        ["add-1998-cmo", "dbl-1998-cmo"],
        "ltr",
        False,
        False,
    )


def test_debug(cli_runner, curve32):
    def callback(target, mult, params):
        model, coords = target.debug()
        assert model == params.curve.model.shortname
        assert coords == params.curve.coordinate_model.name

    do_basic_test(
        callback,
        cli_runner,
        curve32,
        LTRMultiplier,
        ["add-1998-cmo", "dbl-1998-cmo"],
        "ltr",
        False,
        False,
    )


@pytest.mark.parametrize(
    "mult_name,mult_class", [("ltr", LTRMultiplier), ("rtl", RTLMultiplier)]
)
def test_keygen(mult_name, mult_class, cli_runner, curve32):
    def callback(target, mult, params):
        priv, pub = target.generate()
        assert params.curve.is_on_curve(pub)
        expected = mult.multiply(priv).to_affine()
        assert pub == expected

    do_basic_test(
        callback,
        cli_runner,
        curve32,
        mult_class,
        ["add-1998-cmo", "dbl-1998-cmo"],
        mult_name,
        False,
        False,
    )


@pytest.mark.parametrize(
    "mult_name,mult_class", [("ltr", LTRMultiplier), ("rtl", RTLMultiplier)]
)
def test_scalarmult(mult_name, mult_class, cli_runner, curve32):
    values = [2355498743]

    def callback(target, mult, params):
        for value in values:
            result = target.scalar_mult(value, params.generator)
            expected = mult.multiply(value)
            assert result == expected

    do_basic_test(
        callback,
        cli_runner,
        curve32,
        mult_class,
        ["add-1998-cmo", "dbl-1998-cmo"],
        mult_name,
        False,
        False,
    )


@pytest.mark.parametrize(
    "mult_name,mult_class", [("ltr", LTRMultiplier), ("rtl", RTLMultiplier)]
)
def test_ecdh(mult_name, mult_class, cli_runner, curve32):
    other_privs = [2355498743]

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
        curve32,
        mult_class,
        ["add-1998-cmo", "dbl-1998-cmo"],
        mult_name,
        False,
        True,
    )


@pytest.mark.parametrize(
    "mult_name,mult_class", [("ltr", LTRMultiplier), ("rtl", RTLMultiplier)]
)
def test_ecdsa(mult_name, mult_class, cli_runner, curve32):
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
        result = SignatureResult.from_DER(bytes(signature_data))
        assert ecdsa.verify_data(result, data)

        expected = ecdsa.sign_data(data).to_DER()
        assert target.ecdsa_verify(data, expected)

    do_basic_test(
        callback,
        cli_runner,
        curve32,
        mult_class,
        ["add-1998-cmo", "dbl-1998-cmo"],
        mult_name,
        True,
        False,
    )
