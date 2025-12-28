from os import urandom
from base64 import b64encode, b64decode, urlsafe_b64encode
from bcrypt import gensalt, hashpw, checkpw
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from json import dumps, loads


def bcrypt_hash(password: str):
    return hashpw(password.encode(), gensalt()).decode()


def bcrypt_check(password: str, hashed_password: str):
    if not password or not hashed_password:
        return False
    return checkpw(password.encode(), hashed_password.encode())


def generate_salt():
    return b64encode(urandom(16)).decode()


def generate_key(master_password: str, salt: str):
    return urlsafe_b64encode(
        PBKDF2HMAC(SHA256(), 32, b64decode(salt.encode()), 480000).derive(master_password.encode()))


def encrypt_data(data: str, key: bytes):
    return Fernet(key).encrypt(data.encode())


def decrypt_data(data: bytes, key: bytes):
    return Fernet(key).decrypt(data).decode()


def serialize_and_encrypt(data_dict: dict, key: bytes):
    return encrypt_data(dumps(data_dict), key)


def decrypt_and_deserialize(data_dict: bytes, key: bytes):
    return loads(decrypt_data(data_dict, key))
