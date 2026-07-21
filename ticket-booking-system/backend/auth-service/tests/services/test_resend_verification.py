from datetime import datetime

from app.models.email_verification_model import (
    EmailVerificationDocument,
    ResendVerificationRequest,
)
from app.utils.config import settings
import secrets


def test_resend_verification_success(
    auth_service,
    user_repository,
    email_verification_repository,
    notification_client,
    mocker,
):
    # Arrange
    request = ResendVerificationRequest(
        email="john@example.com",
    )

    user = {
        "_id": "user123",
        "email": "john@example.com",
        "username": "john",
        "email_verified": False,
    }

    user_repository.get_by_email.return_value = user

    mocker.patch.object(
        secrets,
        "token_urlsafe",
        return_value="plain_verification_token",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_verification_token",
    )

    fixed_time = datetime(2025, 1, 1, 10, 0, 0)

    mocker.patch.object(
        auth_service,
        "_utc_now",
        return_value=fixed_time,
    )

    # Act
    result = auth_service.resend_verification(request)

    # Assert
    assert (
        result.message
        == "If an account with that email exists, a verification email has been sent."
    )

    user_repository.get_by_email.assert_called_once_with("john@example.com")

    email_verification_repository.revoke_all_by_user_id.assert_called_once_with(
        "user123"
    )

    auth_service._hash_token.assert_called_once_with("plain_verification_token")

    email_verification_repository.save_verification_token.assert_called_once()

    saved_document = (
        email_verification_repository.save_verification_token.call_args.args[0]
    )

    assert isinstance(saved_document, EmailVerificationDocument)

    assert saved_document.user_id == "user123"
    assert saved_document.token == "hashed_verification_token"
    assert saved_document.created_at == fixed_time
    assert saved_document.used is False

    notification_client.send_verification_email.assert_called_once_with(
        recipient="john@example.com",
        name="john",
        verification_link=f"{settings.frontend_url}/verify-email?token=plain_verification_token",
    )


def test_resend_verification_user_not_found(
    auth_service,
    user_repository,
    email_verification_repository,
    notification_client,
):
    # Arrange
    request = ResendVerificationRequest(
        email="unknown@example.com",
    )

    user_repository.get_by_email.return_value = None

    # Act
    result = auth_service.resend_verification(request)

    # Assert
    assert (
        result.message
        == "If an account with that email exists, a verification email has been sent."
    )

    user_repository.get_by_email.assert_called_once_with("unknown@example.com")

    email_verification_repository.revoke_all_by_user_id.assert_not_called()

    email_verification_repository.save_verification_token.assert_not_called()

    notification_client.send_verification_email.assert_not_called()


def test_resend_verification_email_already_verified(
    auth_service,
    user_repository,
    email_verification_repository,
    notification_client,
):
    # Arrange
    request = ResendVerificationRequest(
        email="john@example.com",
    )

    user_repository.get_by_email.return_value = {
        "_id": "user123",
        "email": "john@example.com",
        "username": "john",
        "email_verified": True,
    }

    # Act
    result = auth_service.resend_verification(request)

    # Assert
    assert result.message == "Email is already verified."

    email_verification_repository.revoke_all_by_user_id.assert_not_called()

    email_verification_repository.save_verification_token.assert_not_called()

    notification_client.send_verification_email.assert_not_called()


def test_resend_verification_saves_email_verification_document(
    auth_service,
    user_repository,
    email_verification_repository,
    notification_client,
    mocker,
):
    # Arrange
    request = ResendVerificationRequest(
        email="john@example.com",
    )

    user_repository.get_by_email.return_value = {
        "_id": "user123",
        "email": "john@example.com",
        "username": "john",
        "email_verified": False,
    }

    mocker.patch.object(
        secrets,
        "token_urlsafe",
        return_value="verification_token",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_token",
    )

    fixed_time = datetime(2025, 1, 1, 10, 0, 0)

    mocker.patch.object(
        auth_service,
        "_utc_now",
        return_value=fixed_time,
    )

    # Act
    auth_service.resend_verification(request)

    # Assert
    document = email_verification_repository.save_verification_token.call_args.args[0]

    assert isinstance(document, EmailVerificationDocument)

    assert document.user_id == "user123"
    assert document.token == "hashed_token"
    assert document.created_at == fixed_time
    assert document.used is False


# Resend Verification
#         │
#         ▼
# Find user by email
#         │
#         ├── User not found
#         │        │
#         │        └── Return generic success ✅
#         │
#         ▼
# Already verified?
#         │
#         ├── Yes
#         │      │
#         │      └── Return "Email is already verified." ✅
#         │
#         ▼
# Revoke old verification tokens
#         │
#         ▼
# Generate new token
#         │
#         ▼
# Hash token
#         │
#         ▼
# Save verification token
#         │
#         ▼
# Send verification email
#         │
#         ▼
# Return generic success ✅
