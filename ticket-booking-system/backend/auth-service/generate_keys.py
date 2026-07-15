from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


keys_directory = Path("keys")

keys_directory.mkdir(
    exist_ok=True,
)


private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)


public_key = private_key.public_key()


private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)


public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)


(keys_directory / "private_key.pem").write_bytes(
    private_key_bytes
)


(keys_directory / "public_key.pem").write_bytes(
    public_key_bytes
)


print("RSA key pair generated successfully.")