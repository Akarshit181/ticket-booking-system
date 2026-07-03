# Every request model in FastAPI inherits from BaseModel
# Without BaseModel, FastAPI won't know how to validate incoming JSON
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    username : str = Field(..., min_length=3, max_length=30)
    email : EmailStr
    password : str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email : EmailStr
    password : str

class UserResponse(BaseModel):
    id : str
    username : str
    email : EmailStr