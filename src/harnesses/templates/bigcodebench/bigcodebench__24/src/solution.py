import base64
import hashlib
import os

def task_func(password, SALT_LENGTH = 32):
    """
    Hashes a password using the PBKDF2 HMAC algorithm with SHA-256 as the hashing algorithm, 
    combined with a randomly generated salt, and returns both the salt and the hashed password, 
    each base64-encoded.

    Parameters:
    password (str): The password to be hashed.
    SALT_LENGTH (int): the length of the randomly generated salt.

    Returns:
    tuple[bytes, bytes]: A tuple containing the base64-encoded salt and the base64-encoded hashed password as byte strings.

    Raises:
    ValueError if the password is None or empty

    Requirements:
    - base64
    - hashlib
    - os

    Example:
    >>> salt, hashed_password = task_func('my_password')
    >>> isinstance(salt, bytes)
    True
    >>> isinstance(hashed_password, bytes)
    True
    """
    pass
