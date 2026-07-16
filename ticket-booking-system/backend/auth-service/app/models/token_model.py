from pydantic import BaseModel
from datetime import datetime


class TokenPayload(BaseModel):
    sub: str
    email: str
    role: str
    type: str
    exp: int


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str



class RefreshTokenDocument(BaseModel):
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    is_revoked: bool = False
    revoked_at: datetime | None = None
    replaced_by_token: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str
