import pytest

from app.clients.notification_client import NotificationClient
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.repositories.password_reset_repository import (
    PasswordResetRepository,
)
from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.login_attempt_service import LoginAttemptService


# It tell pytest
# This function provides an object that tests can use. It means whenever a test asks for user_repository, call this function
@pytest.fixture
def user_repository(mocker):
    return mocker.Mock(spec=UserRepository)


@pytest.fixture
def refresh_token_repository(mocker):
    # It creates a mock object instead of real repository. Or we can say we get fake repository
    #     Notice the typo?
    #     mock.get_by_emial()
    #     Python won't complain.
    # Your test still passes.
    # That's dangerous.
    # with spec python knows what method exists.
    return mocker.Mock(spec=RefreshTokenRepository)


@pytest.fixture
def password_reset_repository(mocker):
    return mocker.Mock(spec=PasswordResetRepository)


@pytest.fixture
def email_verification_repository(mocker):
    return mocker.Mock(spec=EmailVerificationRepository)


@pytest.fixture
def login_attempt_service(mocker):
    return mocker.Mock(spec=LoginAttemptService)


@pytest.fixture
def notification_client(mocker):
    return mocker.Mock(spec=NotificationClient)


@pytest.fixture
def auth_service(
    user_repository,
    refresh_token_repository,
    password_reset_repository,
    email_verification_repository,
    login_attempt_service,
    notification_client,
):
    return AuthService(
        user_repository=user_repository,
        refresh_token_repository=refresh_token_repository,
        password_reset_repository=password_reset_repository,
        email_verification_repository=email_verification_repository,
        login_attempt_service=login_attempt_service,
        notification_client=notification_client,
    )


# test_register_user()
#         │
#         ▼
# auth_service
#         │
#         ├─────────────┐
#         ▼             ▼
# user_repository   notification_client
#         │             │
#         ▼             ▼
#       Mock          Mock
# A fixture is simply reusable setup code.
# Instead of creating objects inside every test, you define them once in conftest.py, and pytest injects them into your
# tests automatically, much like FastAPI injects dependencies into your route handlers.
# This makes tests shorter, more consistent, and easier to maintain.
