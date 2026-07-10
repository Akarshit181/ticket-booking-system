# Authentication (Who are you?)
# How does the Booking Service know the user is logged in or not
# The client will send the Authorization Bearer
# The Booking Service must ------- 1) Extract the token 2) Verify the Signature 3) Check if Expired 4) Extract the user_id 5) Continue
# Authentication middleware/dependency
# Client
#     │
# Authorization Header
#     │
#     ▼
# Depends(get_current_user)
#     │
#     ▼
# Decode JWT
#     │
#     ▼
# Verify Signature
#     │
#     ▼
# Verify Expiry
#     │
#     ▼
# Return Payload
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.services.jwt_service import verify_token

# It tells fastapi that every protected endpoint should expects an Authorization header like 
# Authorization: Bearer eyJhbGc... fastapi extracts only this eyJhbGc... 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    token_payload = verify_token(token)
    if token_payload is None: 
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired access token."
        )
    return token_payload
