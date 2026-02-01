def test_hashing():
    from utils.hashing import sha256_hex

    assert len(sha256_hex(b"hi")) == 64
