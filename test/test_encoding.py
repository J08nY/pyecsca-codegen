from pyecsca.ec.mod import Mod
from pyecsca.codegen.client import encode_data, decode_data, encode_scalar


def test_encode_decode():
    data = {
        "a": encode_scalar(0xCAFEBABE),
        "b": {"c": encode_scalar(Mod(1, 3)), "d": bytes([0x2])},
    }
    encoded = encode_data(None, data)
    result = decode_data(encoded)
    assert data == result
