
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-8.4.2, pluggy-1.7.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /content
plugins: langsmith-0.14.17, typeguard-4.6.0, anyio-4.16.0, platformdirs-4.14.3
collecting ... collected 6 items

source/test_negative.py::test_tampered_ciphertext[AESGCM] FAILED         [ 16%]
source/test_negative.py::test_tampered_ciphertext[ChaCha20Poly1305] PASSED [ 33%]
source/test_negative.py::test_tampered_tag[AESGCM] FAILED                [ 50%]
source/test_negative.py::test_tampered_tag[ChaCha20Poly1305] PASSED      [ 66%]
source/test_negative.py::test_tampered_aad[AESGCM] FAILED                [ 83%]
source/test_negative.py::test_tampered_aad[ChaCha20Poly1305] PASSED      [100%]

=================================== FAILURES ===================================
_______________________ test_tampered_ciphertext[AESGCM] _______________________

algorithm = <class 'cryptography.hazmat.bindings._rust.openssl.aead.AESGCM'>

    @pytest.mark.parametrize("algorithm", [AESGCM, ChaCha20Poly1305])
    def test_tampered_ciphertext(algorithm):
>       key = algorithm.generate_key()
              ^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: AESGCM.generate_key() missing 1 required positional argument: 'bit_length'

source/test_negative.py:8: TypeError
__________________________ test_tampered_tag[AESGCM] ___________________________

algorithm = <class 'cryptography.hazmat.bindings._rust.openssl.aead.AESGCM'>

    @pytest.mark.parametrize("algorithm", [AESGCM, ChaCha20Poly1305])
    def test_tampered_tag(algorithm):
>       key = algorithm.generate_key()
              ^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: AESGCM.generate_key() missing 1 required positional argument: 'bit_length'

source/test_negative.py:23: TypeError
__________________________ test_tampered_aad[AESGCM] ___________________________

algorithm = <class 'cryptography.hazmat.bindings._rust.openssl.aead.AESGCM'>

    @pytest.mark.parametrize("algorithm", [AESGCM, ChaCha20Poly1305])
    def test_tampered_aad(algorithm):
>       key = algorithm.generate_key()
              ^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: AESGCM.generate_key() missing 1 required positional argument: 'bit_length'

source/test_negative.py:38: TypeError
=========================== short test summary info ============================
FAILED source/test_negative.py::test_tampered_ciphertext[AESGCM] - TypeError:...
FAILED source/test_negative.py::test_tampered_tag[AESGCM] - TypeError: AESGCM...
FAILED source/test_negative.py::test_tampered_aad[AESGCM] - TypeError: AESGCM...
========================= 3 failed, 3 passed in 0.08s ==========================
