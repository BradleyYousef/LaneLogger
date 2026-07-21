import bcrypt


def hash_password(password):
    """
    Securely hash a password using bcrypt.
    """
    password_bytes = password.encode("utf-8")

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )


def check_password(password, hashed_password):
    """
    Check a plain-text password against a bcrypt hash.
    """
    password_bytes = password.encode("utf-8")

    return bcrypt.checkpw(
        password_bytes,
        hashed_password
    )


def validate_password(password):
    """
    Basic password validation.
    """
    if not password:
        return False

    if len(password) < 8:
        return False

    return True