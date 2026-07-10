from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class ForgotPasswordRequest(BaseModel) : 
    email : EmailStr

class ResetPasswordRequest(BaseModel):
    token : str
    new_password : str = Field(..., min_length=8)

class PasswordResetDocument(BaseModel):
    user_id : str
    token : str
    created_at : datetime
    expires_at : datetime
    used : bool = False

    
    