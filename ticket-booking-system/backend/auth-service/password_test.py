import bcrypt
from passlib.context import CryptContext
import traceback

print("=" * 60)
print("PYTHON / BCRYPT INFO")
print("=" * 60)

print("bcrypt module :", bcrypt)
print("bcrypt file   :", bcrypt.__file__)
print("bcrypt version:", getattr(bcrypt, "__version__", "Not Found"))

print("\n" + "=" * 60)
print("TEST 1 : RAW BCRYPT")
print("=" * 60)

try:
    password = b"Password@123"
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())

    print("SUCCESS")
    print("Password :", password)
    print("Hash     :", hashed.decode())

except Exception:
    print("FAILED")
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST 2 : PASSLIB")
print("=" * 60)

try:
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
    )

    password = "Password@123"

    print("Type      :", type(password))
    print("Value     :", repr(password))
    print("Length    :", len(password))

    hashed = pwd_context.hash(password)

    print("SUCCESS")
    print("Hash :", hashed)

    verified = pwd_context.verify(password, hashed)
    print("Verify :", verified)

except Exception:
    print("FAILED")
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST 3 : LONG PASSWORD (Expected Failure)")
print("=" * 60)

try:
    long_password = "A" * 100

    print("Length :", len(long_password))

    pwd_context.hash(long_password)

    print("Unexpected Success")

except Exception as e:
    print("Expected Exception:")
    print(type(e).__name__)
    print(e)
