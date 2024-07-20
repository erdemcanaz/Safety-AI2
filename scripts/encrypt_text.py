from pathlib import Path
from typing import Dict
import json

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import base64


def derive_key(password: str) -> bytes:
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(password.encode())
    return base64.urlsafe_b64encode(digest.finalize())

def encrypt_string(plain_text: str, password: str) -> str:
    key = derive_key(password)
    cipher_suite = Fernet(key)
    encrypted_text = cipher_suite.encrypt(plain_text.encode())
    return encrypted_text.decode()

def decrypt_string(encrypted_text: str, password: str) -> str:
    key = derive_key(password)
    cipher_suite = Fernet(key)
    decrypted_text = cipher_suite.decrypt(encrypted_text.encode())
    return decrypted_text.decode()

if __name__ == "__main__":
    symmetric_encryption_key = input("Enter a symmetric encryption key: ")
    original_text = input("Enter a text to encrypt: ")

    encrypted_text = encrypt_string(original_text, symmetric_encryption_key)
    decrypted_text = decrypt_string(encrypted_text, symmetric_encryption_key)

    print(f"Symmetric Encryption Key: {symmetric_encryption_key}")
    print(f"Original Text: {original_text}")
    print(f"Encrypted Text: {encrypted_text}")
    print(f"Decrypted Text: {decrypted_text}")

    # Ensure the original and decrypted texts match
    assert original_text == decrypted_text, "The decrypted text does not match the original text!"