import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from main import app
from app.utils.config import settings

from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.password_reset_repository import (
    PasswordResetRepository,
)
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)

from app.dependencies.repository import (
    get_user_repository,
    get_refresh_token_repository,
    get_password_reset_repository,
    get_email_verification_repository,
)

from app.dependencies.provider import get_notification_client


@pytest.fixture(scope="session")
def test_db():
    """
    Creates a dedicated MongoDB database for integration tests.
    The database is dropped once all tests finish.
    """
    client = MongoClient(settings.mongo_uri)

    db = client["auth_service_test"]

    yield db

    client.drop_database("auth_service_test")
    client.close()


@pytest.fixture
def mock_notification_client(mocker):
    """
    Mock NotificationClient that captures verification/reset links
    so integration tests can use the generated tokens.
    """
    mock = mocker.Mock()

    mock.last_reset_link = None
    mock.last_verification_link = None

    def save_reset_email(
        recipient,
        name,
        reset_link,
    ):
        mock.last_reset_link = reset_link

    def save_verification_email(
        recipient,
        name,
        verification_link,
    ):
        mock.last_verification_link = verification_link

    mock.send_password_reset_email.side_effect = save_reset_email
    mock.send_verification_email.side_effect = save_verification_email

    return mock


@pytest.fixture(autouse=True)
def override_dependencies(
    test_db,
    mock_notification_client,
):
    """
    Override production dependencies so integration tests
    use the test database and mocked notification client.
    """

    app.dependency_overrides[get_user_repository] = lambda: UserRepository(test_db)

    app.dependency_overrides[get_refresh_token_repository] = (
        lambda: RefreshTokenRepository(test_db)
    )

    app.dependency_overrides[get_password_reset_repository] = (
        lambda: PasswordResetRepository(test_db)
    )

    app.dependency_overrides[get_email_verification_repository] = (
        lambda: EmailVerificationRepository(test_db)
    )

    app.dependency_overrides[get_notification_client] = lambda: mock_notification_client

    yield

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_database(test_db):
    """
    Ensure every test starts with an empty database.
    """

    for collection_name in test_db.list_collection_names():
        test_db[collection_name].delete_many({})

    yield


@pytest.fixture
def client():
    """
    FastAPI Test Client.
    """
    with TestClient(app) as client:
        yield client
