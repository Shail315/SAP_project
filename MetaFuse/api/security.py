import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta


SESSION_DAYS = 7
PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, rounds, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        rounds_int = int(rounds)
    except Exception:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        rounds_int,
    ).hex()
    return hmac.compare_digest(candidate, digest_hex)


def make_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiry_timestamp() -> str:
    # SQLite CURRENT_TIMESTAMP is UTC in "YYYY-MM-DD HH:MM:SS" format.
    expires = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    return expires.strftime("%Y-%m-%d %H:%M:%S")
