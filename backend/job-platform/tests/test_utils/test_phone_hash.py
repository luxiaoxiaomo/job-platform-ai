"""
手机号哈希工具测试
"""
import pytest
from app.utils.phone_hash import hash_phone


class TestPhoneHash:
    """手机号哈希测试类"""

    def test_hash_phone_deterministic(self):
        """测试phone_hash是确定性的（同一输入产生相同输出）"""
        phone = "13800138000"

        hash1 = hash_phone(phone)
        hash2 = hash_phone(phone)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256输出64位十六进制

    def test_hash_phone_different_inputs(self):
        """测试不同手机号产生不同哈希"""
        phone1 = "13800138000"
        phone2 = "13900139000"

        hash1 = hash_phone(phone1)
        hash2 = hash_phone(phone2)

        assert hash1 != hash2

    def test_hash_phone_normalization(self):
        """测试手机号规范化（去除空格、短横线）"""
        # 这些应该产生相同的哈希
        variations = [
            "13800138000",
            "138 0013 8000",
            "138-0013-8000",
            " 13800138000 ",
        ]

        hashes = [hash_phone(phone) for phone in variations]

        # 所有变体应该产生相同哈希
        assert len(set(hashes)) == 1

    def test_hash_phone_not_reversible(self):
        """测试哈希不可逆（无法从哈希反推手机号）"""
        phone = "13800138000"
        hashed = hash_phone(phone)

        # 哈希值不应该包含原始手机号的任何部分
        assert phone not in hashed
        assert "138" not in hashed
        assert "000" not in hashed
