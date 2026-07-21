from datetime import datetime
from unittest.mock import ANY
from app.models.password_reset_model import PasswordResetDocument, ForgotPasswordRequest
from app.utils.config import settings
import secrets


def test_forgot_password_success(
    auth_service,
    user_repository,
    password_reset_repository,
    notification_client,
    mocker,
):
    # Arrange
    request = ForgotPasswordRequest(
        email="john@example.com",
    )

    user = {
        "_id": "user123",
        "email": "john@example.com",
        "username": "john",
    }

    user_repository.get_by_email.return_value = user

    mocker.patch.object(
        secrets,
        "token_urlsafe",
        return_value="plain_reset_token",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_reset_token",
    )

    fixed_time = datetime(2025, 1, 1, 10, 0, 0)

    mocker.patch.object(
        auth_service,
        "_utc_now",
        return_value=fixed_time,
    )

    # Act
    result = auth_service.forgot_password(request)

    # Assert
    assert result.message == "Reset link sent to your registered email."

    user_repository.get_by_email.assert_called_once_with("john@example.com")

    password_reset_repository.revoke_all_by_user_id.assert_called_once_with("user123")

    auth_service._hash_token.assert_called_once_with("plain_reset_token")

    password_reset_repository.save_reset_token.assert_called_once()

    saved_document = password_reset_repository.save_reset_token.call_args.args[0]

    assert isinstance(saved_document, PasswordResetDocument)

    assert saved_document.user_id == "user123"
    assert saved_document.token == "hashed_reset_token"
    assert saved_document.created_at == fixed_time
    assert saved_document.used is False

    notification_client.send_password_reset_email.assert_called_once_with(
        recipient="john@example.com",
        name="john",
        reset_link=f"{settings.frontend_url}/reset-password?token=plain_reset_token",
    )


def test_forgot_password_email_not_found(
    auth_service,
    user_repository,
    password_reset_repository,
    notification_client,
):
    # Arrange
    request = ForgotPasswordRequest(
        email="unknown@example.com",
    )

    user_repository.get_by_email.return_value = None

    # Act
    result = auth_service.forgot_password(request)

    # Assert
    assert result.message == "Reset link sent to your registered email."

    user_repository.get_by_email.assert_called_once_with("unknown@example.com")

    password_reset_repository.revoke_all_by_user_id.assert_not_called()

    password_reset_repository.save_reset_token.assert_not_called()

    notification_client.send_password_reset_email.assert_not_called()


# Forgot Password
#         │
#         ▼
# Find user by email
#         │
#         ├── User not found
#         │        │
#         │        └── Return success ✅
#         │
#         ▼
# Revoke existing reset tokens
#         │
#         ▼
# Generate reset token
#         │
#         ▼
# Hash token
#         │
#         ▼
# Save reset token
#         │
#         ▼
# Build reset link
#         │
#         ▼
# Send email
#         │
#         ▼
# Return success ✅
