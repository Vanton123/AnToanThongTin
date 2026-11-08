"""test_packet.py - Issue 8: kiem thu pack va unpack (packet.py cua TV3)."""
import os

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

import packet

NONCE = bytes(range(12))
TAG = b"T" * 16


def test_valid_packet():
    data = packet.pack(NONCE, b"hdr", b"abc", TAG)
    assert packet.unpack(data) == (1, NONCE, b"hdr", b"abc", TAG)


def test_empty_aad_and_ciphertext():
    data = packet.pack(NONCE, b"", b"", TAG)
    assert len(data) == 31
    assert packet.unpack(data) == (1, NONCE, b"", b"", TAG)


@pytest.mark.parametrize("algorithm", [AESGCM, ChaCha20Poly1305])
def test_packet_decrypts(algorithm):
    # Ma hoa that, dong goi, tach goi, giai ma ra dung ban ro
    key = os.urandom(32)
    nonce = os.urandom(12)
    out = algorithm(key).encrypt(nonce, b"du lieu", b"hdr")
    data = packet.pack(nonce, b"hdr", out[:-16], out[-16:])
    version, n, aad, ct, tag = packet.unpack(data)
    assert algorithm(key).decrypt(n, ct + tag, aad) == b"du lieu"


def test_truncated_packet_rejected():
    data = packet.pack(NONCE, b"hdr", b"abc", TAG)
    with pytest.raises(ValueError):
        packet.unpack(data[:10])


def test_wrong_version_rejected():
    data = bytearray(packet.pack(NONCE, b"hdr", b"abc", TAG))
    data[0] = 2
    with pytest.raises(ValueError):
        packet.unpack(bytes(data))


def test_wrong_aad_length_rejected():
    data = bytearray(packet.pack(NONCE, b"hdr", b"abc", TAG))
    data[13:15] = (60000).to_bytes(2, "big")  # AAD dai hon ca goi
    with pytest.raises(ValueError):
        packet.unpack(bytes(data))


def test_wrong_nonce_length_rejected():
    with pytest.raises(ValueError):
        packet.pack(b"short", b"hdr", b"abc", TAG)