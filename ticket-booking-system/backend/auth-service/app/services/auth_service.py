from datetime import datetime, UTC
from app.models.user_model import UserRegister, UserLogin
from fastapi import HTTPException

from app.services.password_service import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.services.jwt_service import create_access_token, refresh_access_token


class AuthService:

    def __init__(self):
        self.user_repository = UserRepository()

    def register_user(self, user: UserRegister):

        existing_username = self.user_repository.get_by_username(user.username)

        # db.users.createIndex(
        #     { email: 1 },
        #     { unique: true }
        # )

        # db.users.createIndex(
        #     { username: 1 },
        #     { unique: true }
        # )
        # Do the above to avoid race conditions.

        if existing_username:
            raise HTTPException(status_code=409, detail="Username already exists.")
        existing_email = self.user_repository.get_by_email(user.email)
        if existing_email:
            raise HTTPException(status_code=409, detail="Email already registered.")

        password_hash = hash_password(user.password)

        user_document = {
            "username": user.username,
            "email": user.email,
            "password_hash": password_hash,
            "is_active": True,
            "role": "USER",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        self.user_repository.create(user_document)

        return {
            "message": "User registered successfully.",
        }

    def login_user(self, user: UserLogin):
        existing_email = self.user_repository.get_by_email(user.email)
        if not existing_email:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        password_valid = verify_password(user.password, existing_email["password_hash"])
        if not password_valid:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        payload = {
            "sub": str(existing_email["_id"]),
            "email": existing_email["email"],
            "role": existing_email["role"],
        }

        print(payload)
        print(type(payload))

        access_token = create_access_token(payload)
        refresh_token = refresh_access_token(payload)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
