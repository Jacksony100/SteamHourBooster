from werkzeug.security import check_password_hash, generate_password_hash


HASH_PREFIXES = ("scrypt:", "pbkdf2:", "argon2:", "bcrypt:")


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password is required")
    return generate_password_hash(password)


def is_password_hash(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith(HASH_PREFIXES)


def verify_password(stored_password: str, candidate_password: str) -> bool:
    if not is_password_hash(stored_password):
        return False
    return check_password_hash(stored_password, candidate_password)
