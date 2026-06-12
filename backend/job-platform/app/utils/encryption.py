"""
字段加密工具：使用Fernet对称加密敏感字段
"""
from cryptography.fernet import Fernet

from app.core.config import settings


class FieldEncryptor:
    """字段加密器"""

    def __init__(self):
        """初始化加密器"""
        # 从配置读取密钥
        encryption_key = getattr(settings, "ENCRYPTION_KEY", None)

        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY未配置。请在.env中设置32字节的Fernet密钥。"
                "\n生成方法：python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    def encrypt(self, plaintext: str) -> str:
        """
        加密明文

        Args:
            plaintext: 明文字符串

        Returns:
            密文字符串（Base64编码）
        """
        if not plaintext:
            return ""

        encrypted_bytes = self.fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        解密密文

        Args:
            ciphertext: 密文字符串（Base64编码）

        Returns:
            明文字符串
        """
        if not ciphertext:
            return ""

        decrypted_bytes = self.fernet.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()


# 全局加密器实例
# 初始化失败时直接阻止应用启动（fail-fast）
encryptor = FieldEncryptor()
