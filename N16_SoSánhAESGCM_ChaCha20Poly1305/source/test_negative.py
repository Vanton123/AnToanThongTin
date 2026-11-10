"""test_negative.py - Issue 5, 6: kiem thu am (sua 1 bit) va ca duong cho AES-GCM va ChaCha20-Poly1305."""
import os

import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

ALGORITHMS = [AESGCM, ChaCha20Poly1305]


def make(algorithm):
    """Ma hoa mot ban ro, tra ve (aead, nonce, ban_ro, aad, ban_ma, the)."""
    key = os.urandom(32)
    nonce = os.urandom(12)
    data = b"Payload du lieu quan trong"
    aad = b"Header tin nhan"
    aead = algorithm(key)
    out = aead.encrypt(nonce, data, aad)
    return aead, nonce, data, aad, out[:-16], out[-16:]  # tach ban ma va the


def flip_bit(b):
    """Doi 1 bit o byte dau tien."""
    x = bytearray(b)
    x[0] ^= 0x01
    return bytes(x)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_valid_data_decrypts(algorithm):
    # Ca duong: du lieu nguyen ven thi giai ma ra dung ban ro
    aead, nonce, data, aad, ct, tag = make(algorithm)
    assert aead.decrypt(nonce, ct + tag, aad) == data


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_tampered_ciphertext(algorithm):
    aead, nonce, data, aad, ct, tag = make(algorithm)
    with pytest.raises(InvalidTag):
        aead.decrypt(nonce, flip_bit(ct) + tag, aad)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_tampered_tag(algorithm):
    aead, nonce, data, aad, ct, tag = make(algorithm)
    with pytest.raises(InvalidTag):
        aead.decrypt(nonce, ct + flip_bit(tag), aad)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_tampered_aad(algorithm):
    aead, nonce, data, aad, ct, tag = make(algorithm)
    with pytest.raises(InvalidTag):
        aead.decrypt(nonce, ct + tag, flip_bit(aad))