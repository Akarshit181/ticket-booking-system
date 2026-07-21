from datetime import datetime, UTC, timedelta
from app.models.user_model import UserRegister, UserLogin, ChangePasswordRequest
from fastapi import HTTPException
from app.utils.config import settings
from starlette import status
from app.utils.logger import logger

from app.services import (
    jwt_service,
    password_service,
)
from app.repositories.user_repository import UserRepository

from app.models.token_model import (
    RefreshTokenRequest,
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
from app.services.login_attempt_service import LoginAttemptService
from pymongo.errors import DuplicateKeyError
from app.clients.notification_client import NotificationClient


class AuthService:

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_reset_repository: PasswordResetRepository,
        email_verification_repository: EmailVerificationRepository,
        login_attempt_service: LoginAttemptService,
        notification_client: NotificationClient,
    ):
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository
        self.password_reset_repository = password_reset_repository
        self.email_verification_repository = email_verification_repository
        self.login_attempt_service = login_attempt_service
        self.notification_client = notification_client

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(UTC)

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def register_user(self, user: UserRegister) -> dict:

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
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists.",
            )

        existing_user = self.user_repository.get_by_email(user.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists.",
            )

        password_hash = password_service.hash_password(user.password)
        now = self._utc_now()
        user_document = {
            "username": user.username,
            "email": user.email,
            "email_verified": False,
            "password_hash": password_hash,
            "is_active": True,
            "role": "USER",
            "created_at": now,
            "updated_at": now,
        }

        try:
            created_user = self.user_repository.create(user_document)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists.",
            )

        verification_token = secrets.token_urlsafe(settings.token_bytes)

        token_hash = self._hash_token(verification_token)
        now = self._utc_now()
        verification_document = EmailVerificationDocument(
            user_id=str(created_user.inserted_id),
            token=token_hash,
            created_at=now,
            expires_at=now
            + timedelta(minutes=settings.email_verification_token_expire_minutes),
            used=False,
        )

        self.email_verification_repository.save_verification_token(
            verification_document
        )

        verification_link = (
            f"{settings.frontend_url}/verify-email" f"?token={verification_token}"
        )

        self.notification_client.send_verification_email(
            recipient=user.email,
            name=user.username,
            verification_link=verification_link,
        )

        # Temporary until Notification Service is implemented.
        print(f"Verification Token: {verification_token}")

        return {
            "message": "User registered successfully.",
        }

    def login_user(self, user: UserLogin) -> dict:
        identifier = user.email
        identifier_log_hash = hashlib.sha256(identifier.lower().encode()).hexdigest()[
            :12
        ]
        if self.login_attempt_service.is_blocked(identifier):
            logger.warning(
                "Login blocked due to excessive failed attempts for identifier_hash=%s",
                identifier_log_hash,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )
        existing_user = self.user_repository.get_by_email(user.email)

        if not existing_user:
            self.login_attempt_service.record_failed_attempt(identifier)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        password_valid = password_service.verify_password(
            user.password, existing_user["password_hash"]
        )

        if not password_valid:
            self.login_attempt_service.record_failed_attempt(identifier)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not existing_user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        if not existing_user.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required.",
            )

        self.login_attempt_service.clear_attempts(identifier)

        payload = {
            "sub": str(existing_user["_id"]),
            "email": existing_user["email"],
            "role": existing_user["role"],
        }

        access_token = jwt_service.create_access_token(payload)
        refresh_token = jwt_service.create_refresh_token(payload)
        now = self._utc_now()
        refresh_token_document = RefreshTokenDocument(
            user_id=str(existing_user["_id"]),
            token=self._hash_token(refresh_token),
            created_at=now,
            expires_at=now + timedelta(days=settings.jwt_refresh_token_expire_days),
            is_revoked=False,
        )

        self.refresh_token_repository.save_refresh_token(refresh_token_document)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }

    # This _ means internal helper for this class (Private only availabe for this class only).
    def _save_refresh_token(self, user_id: str, refresh_token: str) -> None:

        now = self._utc_now()
        refresh_token_document = RefreshTokenDocument(
            user_id=user_id,
            token=self._hash_token(refresh_token),
            created_at=now,
            expires_at=now + timedelta(days=settings.jwt_refresh_token_expire_days),
            is_revoked=False,
        )

        self.refresh_token_repository.save_refresh_token(refresh_token_document)

    def refresh_access_token(self, token_request: RefreshTokenRequest):
        token_payload = jwt_service.verify_token(
            token_request.refresh_token,
            token_type="refresh",
        )

        if token_payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        refresh_token_hash = self._hash_token(token_request.refresh_token)
        existing_refresh_token = self.refresh_token_repository.find_by_token(
            refresh_token_hash
        )

        if existing_refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        if existing_refresh_token["is_revoked"]:

            revocation_reason = existing_refresh_token.get("revocation_reason")

            if revocation_reason == "rotation":
                self.refresh_token_repository.revoke_all_by_user_id(
                    existing_refresh_token["user_id"]
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        user = self.user_repository.get_by_id(token_payload.sub)

        if not user:
            self.refresh_token_repository.revoke_all_by_user_id(token_payload.sub)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        if not user.get("is_active", True):
            self.refresh_token_repository.revoke_all_by_user_id(token_payload.sub)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        if not user.get("email_verified", False):
            self.refresh_token_repository.revoke_all_by_user_id(token_payload.sub)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required.",
            )

        payload = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
        }

        access_token = jwt_service.create_access_token(payload)
        new_refresh_token = jwt_service.create_refresh_token(payload)

        new_refresh_token_hash = self._hash_token(new_refresh_token)

        consumed_token = self.refresh_token_repository.consume_for_rotation(
            refresh_token_hash,
            new_refresh_token_hash,
        )

        if consumed_token is None:
            self.refresh_token_repository.revoke_all_by_user_id(str(user["_id"]))

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        self._save_refresh_token(
            str(user["_id"]),
            new_refresh_token,
        )

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
    def logout(self, logout_request: LogoutRequest) -> dict:
        token_payload = jwt_service.verify_token(
            logout_request.refresh_token, token_type="refresh"
        )
        if token_payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )
        refresh_token_hash = self._hash_token(logout_request.refresh_token)
        existing_refresh_token = self.refresh_token_repository.find_by_token(
            refresh_token_hash
        )

        if existing_refresh_token:
            self.refresh_token_repository.revoke_for_logout(refresh_token_hash)

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
    ) -> dict:
        user = self.user_repository.get_by_id(current_user.sub)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )

        if not password_service.verify_password(
            request.old_password, user["password_hash"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect.",
            )
        # This compares against the stored hash, making it robust even if password handling changes in the future.
        if password_service.verify_password(
            request.new_password, user["password_hash"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the old password.",
            )

        new_password_hash = password_service.hash_password(request.new_password)

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
    def forgot_password(self, request: ForgotPasswordRequest) -> dict:
        user = self.user_repository.get_by_email(request.email)
        if not user:
            return MessageResponse(message="Reset link sent to your registered email.")

        self.password_reset_repository.revoke_all_by_user_id(str(user["_id"]))
        reset_token = secrets.token_urlsafe(settings.token_bytes)

        token_hash = self._hash_token(reset_token)
        now = self._utc_now()
        reset_document = PasswordResetDocument(
            user_id=str(user["_id"]),
            token=token_hash,
            created_at=now,
            expires_at=now
            + timedelta(minutes=settings.password_reset_token_expire_minutes),
            used=False,
        )

        self.password_reset_repository.save_reset_token(reset_document)

        reset_link = f"{settings.frontend_url}/reset-password" f"?token={reset_token}"

        self.notification_client.send_password_reset_email(
            recipient=user["email"],
            name=user["username"],
            reset_link=reset_link,
        )

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
    def reset_password(self, request: ResetPasswordRequest) -> dict:
        token_hash = self._hash_token(request.token)

        reset_token = self.password_reset_repository.consume_token(token_hash)

        if reset_token is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )

        new_password_hash = password_service.hash_password(request.new_password)

        self.user_repository.update_password(
            reset_token["user_id"],
            new_password_hash,
        )

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

    def verify_email(self, request: VerifyEmailRequest) -> dict:
        token_hash = self._hash_token(request.token)
        verification_token = self.email_verification_repository.consume_token(
            token_hash
        )

        if verification_token is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token.",
            )

        result = self.user_repository.update_email_verified(
            verification_token["user_id"]
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to verify email.",
            )

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

    def resend_verification(self, request: ResendVerificationRequest) -> dict:

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
        verification_token = secrets.token_urlsafe(settings.token_bytes)

        # Store only the SHA-256 hash.
        token_hash = self._hash_token(verification_token)
        now = self._utc_now()
        verification_document = EmailVerificationDocument(
            user_id=str(user["_id"]),
            token=token_hash,
            created_at=now,
            expires_at=now
            + timedelta(minutes=settings.email_verification_token_expire_minutes),
            used=False,
        )

        self.email_verification_repository.save_verification_token(
            verification_document
        )

        verification_link = (
            f"{settings.frontend_url}/verify-email" f"?token={verification_token}"
        )

        self.notification_client.send_verification_email(
            recipient=user["email"],
            name=user["username"],
            verification_link=verification_link,
        )
        print(f"Verification Token: {verification_token}")

        return MessageResponse(
            message="If an account with that email exists, a verification email has been sent."
        )
