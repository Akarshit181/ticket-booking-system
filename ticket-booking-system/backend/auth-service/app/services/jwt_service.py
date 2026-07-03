# JWT (JSON Web Token) Service
# A JWT has three parts: Header, Payload, and Signature. The header and payload are base64 encoded JSON objects. The signature is created by signing the header and payload with a secret key using a specified algorithm.
# JWT defines a standard claim called Subject (sub). as sub contains mongodb_user_id as it is unique as email can be changed by user but mongodb_user_id is unique and never changes. So we use sub to store mongodb_user_id.

# python-jose provide jwt.encode(...) and jwt.decode(...) methods to create and verify JWTs.
# python-jose creates the Header and Signature automatically. You only provide the payload.
# The signature is not random.

# It depends on

# Header
# Payload
# Secret Key
# When user send any data it again creates the signature using the same Header, Payload, and Secret Key. If the signature matches the one in the JWT, it means the data has not been tampered with.

from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from app.utils.config import settings


def create_access_token(data: dict):
    # we don't want to modify the original data dictionary show we work on a copy of it. This is important because dictionaries are mutable in Python, and modifying the original dictionary could lead to unexpected behavior elsewhere in the code.
    payload = data.copy()
    # Adding Expiration
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    # Now payload becomes sub, role, exp. The exp is a standard claim that indicates the expiration time of the token. It is used to determine if the token is still valid or has expired.
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def refresh_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        return payload
    except JWTError:
        return None

def verify_token(token: str):
    payload = decode_token(token)

    if payload is None:
        return None
    return payload
