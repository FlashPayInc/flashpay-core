from base64 import b64decode

from cryptography.fernet import Fernet

from django.conf import settings


def decrypt_fernet_message(payload: str) -> str:
    """Takes a base64 encoded Fernet encrypted message and decrypts it.

    May raise:
    - binascii.Error
    - InvalidToken
    """
    b64_decoded_payload = b64decode(payload.encode())
    fernet = Fernet(settings.ENCRYPTION_KEY.encode())
    decrypted_payload = fernet.decrypt(b64_decoded_payload).decode()

    return str(decrypted_payload)
