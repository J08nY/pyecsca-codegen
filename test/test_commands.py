from pyecsca.codegen.client import (
    cmd_init_prng,
    cmd_set_params,
    cmd_set_pubkey,
    cmd_set_privkey,
    cmd_scalar_mult,
    cmd_ecdh,
    cmd_ecdsa_sign,
    cmd_ecdsa_verify,
    cmd_generate,
    cmd_debug,
    cmd_set_trigger,
    Triggers,
)


def test_init_prng():
    assert cmd_init_prng(bytes([0xCA, 0xFE, 0xBA, 0xBE])) is not None


def test_set_curve(secp128r1):
    assert cmd_set_params(secp128r1) is not None


def test_generate():
    assert cmd_generate() is not None


def test_set_pubkey(secp128r1):
    assert cmd_set_pubkey(secp128r1.generator) is not None


def test_set_privkey():
    assert cmd_set_privkey(0x123456789) is not None


def test_scalar_mult(secp128r1):
    assert cmd_scalar_mult(0x123456789, secp128r1.generator) is not None


def test_ecdh(secp128r1):
    assert cmd_ecdh(secp128r1.generator) is not None


def test_ecdsa_sign():
    assert cmd_ecdsa_sign(b"something") is not None


def test_ecdsa_verify():
    assert cmd_ecdsa_verify(b"something", b"signature") is not None


def test_set_trigger():
    assert cmd_set_trigger(Triggers.add) is not None


def test_debug():
    assert cmd_debug() is not None
