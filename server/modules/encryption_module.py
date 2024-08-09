from pathlib import Path
from typing import Dict
import json, hashlib, platform

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import base64

# Load user database
ENCRPYTION_MODULE_PATH = Path(__file__).resolve()

is_linux = platform.system() == "Linux"
if is_linux:
    USER_DATABASE_JSON_PATH = ENCRPYTION_MODULE_PATH.parent.parent.parent.parent / "safety_AI_volume" / "static_database.json"
else:
    USER_DATABASE_JSON_PATH = ENCRPYTION_MODULE_PATH.parent.parent / "configs" / "static_database.json"

with open(USER_DATABASE_JSON_PATH, "r") as f:
    SYMMETRIC_ENCRYPTION_KEY = json.load(f)["symmetric_encryption_key"]

# Function to derive a key from the known string
def derive_key(password: str) -> bytes:
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(password.encode())
    return base64.urlsafe_b64encode(digest.finalize())

# Encrypt the string
def encrypt_string(plain_text: str, password: str) -> str:
    key = derive_key(password)
    cipher_suite = Fernet(key)
    encrypted_text = cipher_suite.encrypt(plain_text.encode())
    return encrypted_text.decode()

# Decrypt the string
def decrypt_string(encrypted_text: str, password: str = None) -> str:
    if password is not None:
        key = derive_key(password)
    else:
        key = derive_key(SYMMETRIC_ENCRYPTION_KEY)

    cipher_suite = Fernet(key)
    decrypted_text = cipher_suite.decrypt(encrypted_text.encode())
    return decrypted_text.decode()

def hash_string(plain_text:str=""):
    # Create a new SHA256 hash object
    sha256_hash = hashlib.sha256()

    # Convert the plain text to bytes and update the hash object
    sha256_hash.update(plain_text.encode('utf-8'))

    # Get the hashed password as a hexadecimal string
    hashed_password = sha256_hash.hexdigest()

    return hashed_password

# Example usage
if __name__ == "__main__":
    original_text = input("Enter original text: ")
    symmetric_encryption_key = SYMMETRIC_ENCRYPTION_KEY

    print(f"Original Text: {original_text}")

    # Encrypt the string
    encrypted_text = encrypt_string(original_text, symmetric_encryption_key)
    print(f"Encrypted Text: {encrypted_text}")

    # Decrypt the string
    decrypted_text = decrypt_string(encrypted_text, symmetric_encryption_key)
    print(f"Decrypted Text: {decrypted_text}")

    hashed_text = hash_string(symmetric_encryption_key)
    print(f"Hashed Text: ")

    # Ensure the original and decrypted texts match
    assert original_text == decrypted_text, "The decrypted text does not match the original text!"