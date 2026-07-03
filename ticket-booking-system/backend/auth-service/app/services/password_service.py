# passlib provide secured password hashing. It supports many algorithms like bycrpt, argon2, pbkdf2, scrypt
from passlib.context import CryptContext


# bcrypt.hashpw(...) we are not using this as:
# why deprecated auto : Suppose in future you switch one algorithm to another passlib can recognize and help to manage older hashes while new one use the updated algorithm

pwd_Context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The same password never produce the same hash because bcrypt generates random salt each time.
def hash_password(password: str) -> str:
    return pwd_Context.hash(password)


# bcrypt doesn't compare hashes. It uses the salt stored inside the hash itself. It extract the salt from hashed password and create the hash of plain password then compare it 
# A bcrypt has actually contains:
# Algorithm
# Cost Factor 
# Salt 
# Hash
def verify_password(
    plain_password: str,
    hash_password: str,
) -> bool:
    return pwd_Context.verify(plain_password, hash_password)
