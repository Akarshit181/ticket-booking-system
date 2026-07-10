# This module provides a dependency for the AuthService class. It defines a function get_auth_service that returns an instance of AuthService. This can be used in other parts of the application to access authentication-related functionality.
# Instead of creating an object yourself, you ask FastAPI to provide it when needed.
# Without DI (auth_service = AuthService()) you are saying you will create it with DI (auth_service: AuthService = Depends(get_auth_service)) you are saying you will provide it when needed. This is useful for testing and for decoupling components of your application.
# Nothing special.

# It simply returns an object.
from fastapi import Depends

from app.services.auth_service import AuthService

from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.email_verification_repository import EmailVerificationRepository

from app.dependencies.repository import (
    get_refresh_token_repository,
    get_password_reset_repository,
    get_email_verification_repository,
)


def get_auth_service(
    refresh_token_repository: RefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
    password_reset_repository: PasswordResetRepository = Depends(
        get_password_reset_repository
    ),
    email_verification_repository: EmailVerificationRepository = Depends(
        get_email_verification_repository
    ),
):
    return AuthService(
        refresh_token_repository=refresh_token_repository,
        password_reset_repository=password_reset_repository,
        email_verification_repository=email_verification_repository,
    )
