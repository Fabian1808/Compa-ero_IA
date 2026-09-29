from cryptography.fernet import Fernet
import keyring
import base64
import os
from app.config import settings


class TokenEncryption:
    """Encryption for OAuth tokens using Fernet with key from OS keyring."""

    SERVICE_NAME = "ai-workmate"
    KEY_ID = "master-key"

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._fernet: Fernet | None = None

    def _get_or_create_key(self) -> bytes:
        key_b64 = keyring.get_password(self.SERVICE_NAME, f"{self.KEY_ID}-{self.user_id}")

        if key_b64:
            return base64.urlsafe_b64decode(key_b64)

        key = Fernet.generate_key()
        keyring.set_password(self.SERVICE_NAME, f"{self.KEY_ID}-{self.user_id}", base64.urlsafe_b64encode(key).decode())
        return key

    @property
    def fernet(self) -> Fernet:
        if self._fernet is None:
            self._fernet = Fernet(self._get_or_create_key())
        return self._fernet

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        return self.fernet.decrypt(encrypted.encode()).decode()


def get_encryption(user_id: str) -> TokenEncryption:
    return TokenEncryption(user_id)