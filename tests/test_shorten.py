"""Unit tests for base62 encoding/decoding — no database required."""
import pytest

from app.utils.base62 import decode_base62, encode_base62

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class TestEncode:
    def test_zero(self):
        assert encode_base62(0) == "0"

    def test_known_value(self):
        # 125 = 2 * 62 + 1  →  "21"
        assert encode_base62(125) == "21"

    def test_large_number(self):
        result = encode_base62(3844)  # 62^2  →  "100"
        assert result == "100"

    def test_uses_only_base62_chars(self):
        for n in [1, 61, 62, 999, 12345, 999999]:
            for ch in encode_base62(n):
                assert ch in BASE62

    def test_monotone(self):
        """Larger id must produce a different (larger) encoding."""
        assert encode_base62(1) != encode_base62(2)


class TestDecode:
    def test_roundtrip(self):
        for n in [0, 1, 61, 62, 125, 3843, 3844, 12345]:
            assert decode_base62(encode_base62(n)) == n

    def test_known_value(self):
        assert decode_base62("21") == 125

    def test_single_char(self):
        assert decode_base62("0") == 0
        assert decode_base62("Z") == 61


class TestInvalidInput:
    def test_invalid_char_raises(self):
        with pytest.raises((ValueError, KeyError)):
            decode_base62("!!")
