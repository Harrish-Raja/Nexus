"""Turns a password into the salted form the database stores."""

import hashlib

from config import config


def hash_password(plain_password, password_salt):
    """PBKDF2 of the password with this account's own salt, returned as hex text."""
    digest = hashlib.pbkdf2_hmac(config.PASSWORD_HASH_ALGORITHM,
                                 str(plain_password).encode("utf-8"),
                                 str(password_salt).encode("utf-8"),
                                 config.PASSWORD_HASH_ROUNDS)
    return digest.hex()
