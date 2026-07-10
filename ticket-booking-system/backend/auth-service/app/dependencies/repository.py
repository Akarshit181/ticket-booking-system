from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)


def get_user_repository():
    return UserRepository()


def get_refresh_token_repository():
    return RefreshTokenRepository()


def get_password_reset_repository():
    return PasswordResetRepository()


def get_email_verification_repository():
    return EmailVerificationRepository()
