import pytest
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.exceptions import InvalidTag

@pytest.mark.parametrize("algorithm", [AESGCM, ChaCha20Poly1305])
def test_tampered_ciphertext(algorithm):
    key = algorithm.generate_key()
    aead = algorithm(key)
    nonce = os.urandom(12)
    data = b"Payload du lieu quan trong"
    aad = b"Header tin nhan"

    # Ma hoa
    ct = aead.encrypt(nonce, data, aad)
    
    # Kich ban 1: Doi 1 bit o ban ma (Ciphertext)
    tampered_ct = bytearray(ct)
    tampered_ct[0] ^= 0x01

    with pytest.raises(InvalidTag):
        aead.decrypt(nonce, bytes(tampered_ct), aad)

@pytest.mark.parametrize("algorithm", [AESGCM, ChaCha20Poly1305])
def test_tampered_tag(algorithm):
    key = algorithm.generate_key()
    aead = algorithm(key)
    nonce = os.urandom(12)
    data = b"Payload du lieu quan trong"
    aad = b"Header tin nhan"

    ct = aead.encrypt(nonce, data, aad)

    # Kich ban 2: Doi 1 bit o Authentication Tag (16 byte cuoi)
    tampered_tag = bytearray(ct)
    tampered_tag[-1] ^= 0x01

    with pytest.raises(InvalidTag):
        aead.decrypt(nonce, bytes(tampered_tag), aad)

@pytest.mark.parametrize("algorithm", [AESGCM, ChaCha20Poly1305])
def test_tampered_aad(algorithm):
    key = algorithm.generate_key()
    aead = algorithm(key)
    nonce = os.urandom(12)
    data = b"Payload du lieu quan trong"
    aad = b"Header tin nhan"

    ct = aead.encrypt(nonce, data, aad)

    # Kich ban 3: Doi 1 bit o Du lieu kem theo (AAD)
    tampered_aad = bytearray(aad)
    tampered_aad[0] ^= 0x01

    with pytest.raises(InvalidTag):
        aead.decrypt(nonce, ct, bytes(tampered_aad))
