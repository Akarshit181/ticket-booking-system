from datetime import datetime, UTC, timedelta
from app.models.user_model import UserRegister, UserLogin, ChangePasswordRequest
from fastapi import HTTPException
from app.utils.config import settings

from app.services.password_service import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.services.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.models.token_model import (
    RefreshTokenRequest,
    AccessTokenResponse,
    RefreshTokenDocument,
    TokenResponse,
    LogoutRequest,
    TokenPayload,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.models.response_model import MessageResponse
from app.models.password_reset_model import (
    ForgotPasswordRequest,
    PasswordResetDocument,
    ResetPasswordRequest,
)
from app.repositories.password_reset_repository import PasswordResetRepository

import secrets
import hashlib
from app.models.email_verification_model import (
    EmailVerificationDocument,
    ResendVerificationRequest,
    VerifyEmailRequest,
)
from app.repositories.email_verification_repository import EmailVerificationRepository

reset_token = secrets.token_urlsafe(32)


class AuthService:

    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        password_reset_repository: PasswordResetRepository,
        email_verification_repository: EmailVerificationRepository,
    ):
        self.user_repository = UserRepository()

        self.refresh_token_repository = refresh_token_repository
        self.password_reset_repository = password_reset_repository
        self.email_verification_repository = email_verification_repository

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
        existing_user = self.user_repository.get_by_email(user.email)
        if existing_user:
            raise HTTPException(status_code=409, detail="Email already registered.")

        password_hash = hash_password(user.password)

        user_document = {
            "username": user.username,
            "email": user.email,
            "email_verified": False,
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
        existing_user = self.user_repository.get_by_email(user.email)
        if not existing_user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        password_valid = verify_password(user.password, existing_user["password_hash"])
        if not password_valid:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        payload = {
            "sub": str(existing_user["_id"]),
            "email": existing_user["email"],
            "role": existing_user["role"],
        }

        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        refresh_token_document = RefreshTokenDocument(
            user_id=str(existing_user["_id"]),
            token=refresh_token,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.jwt_refresh_token_expire_days),
            is_revoked=False,
        )

        self.refresh_token_repository.save_refresh_token(refresh_token_document)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }

    # This _ means internal helper for this class (Private only availabe for this class only).
    def _save_refresh_token(self, user_id: str, refresh_token: str):

        refresh_token_document = RefreshTokenDocument(
            user_id=user_id,
            token=refresh_token,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.jwt_refresh_token_expire_days),
            is_revoked=False,
        )

        self.refresh_token_repository.save_refresh_token(refresh_token_document)

    def refresh_access_token(self, token_request: RefreshTokenRequest):
        token_payload = verify_token(token_request.refresh_token, token_type="refresh")
        existing_refresh_token = self.refresh_token_repository.find_by_token(
            token_request.refresh_token
        )
        if existing_refresh_token is None:
            raise HTTPException(
                status_code=401,
                detail="Refresh token has been revoked or does not exist.",
            )
        if token_payload is None:
            raise HTTPException(
                status_code=401, detail="Invalid or expired refresh token."
            )
        payload = {
            "sub": token_payload.sub,
            "email": token_payload.email,
            "role": token_payload.role,
        }
        access_token = create_access_token(payload)
        new_refresh_token = create_refresh_token(payload)
        self.refresh_token_repository.delete_token(token_request.refresh_token)
        self._save_refresh_token(token_payload.sub, new_refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    # Client
    #    │
    #    ▼
    # POST /auth/logout
    #    │
    #    ▼
    # Send Refresh Token
    #    │
    #    ▼
    # Verify JWT
    #    │
    #    ▼
    # Find Refresh Token in MongoDB
    #    │
    #    ▼
    # Delete Refresh Token
    #    │
    #    ▼
    # Return Success
    def logout(self, logout_request: LogoutRequest):
        token_payload = verify_token(logout_request.refresh_token, token_type="refresh")
        if token_payload is None:
            raise HTTPException(
                status_code=401, detail="Invalid or expired refresh token."
            )

        existing_refresh_token = self.refresh_token_repository.find_by_token(
            logout_request.refresh_token
        )

        if existing_refresh_token:
            self.refresh_token_repository.delete_token(logout_request.refresh_token)

        return {"message": "Logged out successfully."}

    #     JWT
    #  │
    #  ▼
    # current_user.sub
    #  │
    #  ▼
    # UserRepository.get_by_id()
    #  │
    #  ▼
    # Verify Old Password
    #  │
    #  ▼
    # Verify New Password is Different
    #  │
    #  ▼
    # Hash Password
    #  │
    #  ▼
    # UserRepository.update_password()
    #  │
    #  ▼
    # RefreshTokenRepository.delete_all_by_user_id()
    #  │
    #  ▼
    # Return Success

    def change_password(
        self, current_user: TokenPayload, request: ChangePasswordRequest
    ):
        user = self.user_repository.get_by_id(current_user.sub)

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        if not verify_password(request.old_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Old password is incorrect.")
        # This compares against the stored hash, making it robust even if password handling changes in the future.
        if verify_password(request.new_password, user["password_hash"]):
            raise HTTPException(
                status_code=400,
                detail="New password must be different from the old password.",
            )

        new_password_hash = hash_password(request.new_password)

        self.user_repository.update_password(current_user.sub, new_password_hash)

        self.refresh_token_repository.delete_all_by_user_id(current_user.sub)

        return MessageResponse(
            message="Password changed successfully. Please login again."
        )

    # Receive Email
    #       │
    #       ▼
    # Find User
    #       │
    #       ▼
    # User Exists?
    #       │
    #  ┌────┴────┐
    #  │         │
    # Yes        No
    #  │         │
    # Generate    Return Generic Message
    # Token
    #  │
    #  ▼
    # Save Token
    #  │
    #  ▼
    # Call Notification Service (later)
    #  │
    #  ▼
    # Return Generic Message
    def forgot_password(self, request: ForgotPasswordRequest):
        user = self.user_repository.get_by_email(request.email)
        if not user:
            MessageResponse(message="Reset link sent to your registered email.")
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
        reset_document = PasswordResetDocument(
            user_id=str(user["_id"]),
            token=token_hash,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.password_reset_token_expire_minutes),
            used=False,
        )

        self.password_reset_repository.save_reset_token(reset_token)

        print(reset_token)

        #         notification_client.send_password_reset(
        #     ...
        # )

        return MessageResponse(message="Reset link sent to your registered email.")

    # Receive Token
    #       │
    #       ▼
    # Find Token
    #       │
    #       ▼
    # Token Valid?
    #       │
    #       ▼
    # Find User
    #       │
    #       ▼
    # Hash Password
    #       │
    #       ▼
    # Update Password
    #       │
    #       ▼
    # Mark Reset Token Used
    #       │
    #       ▼
    # Delete All Refresh Tokens
    #       │
    #       ▼
    # Return Success
    def reset_password(self, request: ResetPasswordRequest):
        token_hash = hashlib.sha256(request.token.encode()).hexdigest()
        reset_token = self.password_reset_repository.find_by_token_hash(token_hash)

        if reset_token is None:
            raise HTTPException(
                status_code=400, detail="Invalid or expired reset token."
            )

        if reset_token["expires_at"] < datetime.now(UTC):
            raise HTTPException(
                status_code=400, detail="Invalid or expired reset token."
            )

        # when want soft delete or deactivate account
        # user = self.user_repository.get_by_id(reset_token["user_id"])

        new_password_hash = hash_password(request.new_password)

        self.user_repository.update_password(reset_token["user_id"], new_password_hash)

        self.password_reset_repository.mark_as_used(token_hash)

        self.refresh_token_repository.delete_all_by_user_id(reset_token["user_id"])

        return MessageResponse(
            message="Password reset successfully. Please login again."
        )

    # User Clicks Verification Link
    #             │
    #             ▼
    # Receive Token
    #             │
    #             ▼
    # Hash Token
    #             │
    #             ▼
    # Find Token in MongoDB
    #             │
    #             ▼
    # Token Exists?
    #             │
    #             ▼
    # Expired?
    #             │
    #             ▼
    # Mark User as Verified
    #             │
    #             ▼
    # Mark Token as Used
    #             │
    #             ▼
    # Return Success

    def verify_email(self, request: VerifyEmailRequest):
        token_hash = hashlib.sha256(request.token.encode()).hexdigest()
        verification_token = self.email_verification_repository.find_by_token_hash(
            token_hash
        )

        if verification_token is None:
            raise HTTPException(
                status_code=400, detail="Invalid or expired verification token."
            )

        if verification_token["expires_at"] < datetime.now(UTC):
            raise HTTPException(
                status_code=400, detail="Invalid or expired verification token."
            )

        result = self.user_repository.update_email_verified(
            verification_token["user_id"]
        )

        self.email_verification_repository.mark_as_used(token_hash)

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Unable to verify email.")

        return MessageResponse(message="Email verified successfully.")


# Receive Email
#       │
#       ▼
# Find User
#       │
#       ▼
# User Exists?
#       │
#  ┌────┴────┐
#  │         │
# No        Yes
#  │         │
# Return     Already Verified?
# Success        │
#                ▼
#            Yes ─────────► Return "Email already verified."
#                │
#                ▼
#       Generate Verification Token
#                │
#                ▼
#             Hash Token
#                │
#                ▼
#       Save Verification Token
#                │
#                ▼
#     Notification Service (Later)
#                │
#                ▼
#          Return Success


def resend_verification(self, request: ResendVerificationRequest):

    user = self.user_repository.get_by_email(request.email)

    # Don't reveal whether the email exists.
    if user is None:
        return MessageResponse(
            message="If an account with that email exists, a verification email has been sent."
        )

    # Email is already verified.
    if user["email_verified"]:
        return MessageResponse(message="Email is already verified.")

    # Revoke all previous unused verification tokens.
    self.email_verification_repository.revoke_all_by_user_id(str(user["_id"]))

    # Generate a new verification token.
    verification_token = secrets.token_urlsafe(32)

    # Store only the SHA-256 hash.
    token_hash = hashlib.sha256(verification_token.encode()).hexdigest()

    verification_document = EmailVerificationDocument(
        user_id=str(user["_id"]),
        token=token_hash,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC)
        + timedelta(minutes=settings.email_verification_token_expire_minutes),
        used=False,
    )

    self.email_verification_repository.save_verification_token(verification_document)

    # TODO:
    # notification_client.send_verification_email(
    #     email=user["email"],
    #     username=user["username"],
    #     verification_token=verification_token,
    # )

    # Temporary until Notification Service is implemented.
    print(f"Verification Token: {verification_token}")

    return MessageResponse(
        message="If an account with that email exists, a verification email has been sent."
    )

