"""packet.py - Issue 11: dong goi va giai goi du lieu.

Thu tu truong:
    phien ban (1 byte) | nonce (12 byte) | do dai AAD (2 byte) | AAD | ban ma | the (16 byte)
"""

VERSION = 1
NONCE_LEN = 12
TAG_LEN = 16
HEADER_LEN = 1 + NONCE_LEN + 2      # 15 byte truoc AAD
MIN_LEN = HEADER_LEN + TAG_LEN      # 31 byte (AAD rong, ban ma rong)


def pack(nonce, aad, ciphertext, tag):
    """Ghep cac truong thanh mot goi (bytes)."""
    if len(nonce) != NONCE_LEN:
        raise ValueError("nonce phai dai 12 byte")
    if len(tag) != TAG_LEN:
        raise ValueError("the phai dai 16 byte")
    if len(aad) > 65535:
        raise ValueError("AAD dai qua 65535 byte")
    return (bytes([VERSION]) + nonce + len(aad).to_bytes(2, "big")
            + aad + ciphertext + tag)


def unpack(data):
    """Tach goi thanh (version, nonce, aad, ciphertext, tag).
    Goi sai thi nem ValueError. Ham nay CHUA xac thuc: chi giai ma khi the hop le."""
    if len(data) < MIN_LEN:
        raise ValueError("goi qua ngan")
    version = data[0]
    if version != VERSION:
        raise ValueError("sai phien ban")
    nonce = data[1:13]
    aad_len = int.from_bytes(data[13:15], "big")
    if HEADER_LEN + aad_len + TAG_LEN > len(data):
        raise ValueError("do dai AAD sai")
    aad = data[HEADER_LEN:HEADER_LEN + aad_len]
    ciphertext = data[HEADER_LEN + aad_len:-TAG_LEN]
    tag = data[-TAG_LEN:]
    return version, nonce, aad, ciphertext, tag