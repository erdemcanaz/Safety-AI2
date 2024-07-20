import hashlib

def hash_text(plain_text):
    # Create a new SHA256 hash object
    sha256_hash = hashlib.sha256()

    # Convert the plain text to bytes and update the hash object
    sha256_hash.update(plain_text.encode('utf-8'))

    # Get the hashed password as a hexadecimal string
    hashed_password = sha256_hash.hexdigest()

    return hashed_password

# Example usage
text_to_hash = input("Enter a text to hash (SHA256): ")
hashed_password = hash_text(text_to_hash)
print("Original text:", text_to_hash)
print("Hashed text:", hashed_password)