from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _get_fernet() -> Fernet:
    try:
        return Fernet(settings.encryption_key.encode())
    except Exception as exc:  # pragma: no cover - misconfiguration case
        raise ValueError("Invalid ENCRYPTION_KEY; must be a valid Fernet base64 key") from exc


fernet = _get_fernet()


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext value using Fernet symmetric encryption."""
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext value using Fernet symmetric encryption."""
    try:
        return fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt value") from exc
