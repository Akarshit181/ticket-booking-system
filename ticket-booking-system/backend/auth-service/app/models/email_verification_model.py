from pydantic import BaseModel, EmailStr
from datetime import datetime, UTC


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationDocument(BaseModel):
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    used: bool = False
