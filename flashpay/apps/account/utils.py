import hashlib
import secrets
from typing import Tuple


def generate_api_key(address: str, network: str) -> Tuple[str, str]:
    secret_key = secrets.token_hex()
    hashed_addr = hashlib.md5(address.encode()).hexdigest()
    public_key = hashlib.sha256(f"{hashed_addr}{secret_key}".encode()).hexdigest()
    if network == "testnet":
        secret_key = f"sk_test_{secret_key}"
        public_key = f"pk_test_{public_key}"
    else:
        secret_key = f"sk_{secret_key}"
        public_key = f"pk_{public_key}"
    return secret_key, public_key
