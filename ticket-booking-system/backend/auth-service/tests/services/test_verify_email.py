import pytest
from fastapi import HTTPException

from app.models.email_verification_model import VerifyEmailRequest


def test_verify_email_success(
    auth_service,
    user_repository,
    email_verification_repository,
    mocker,
):
    # Arrange
    request = VerifyEmailRequest(
        token="plain_verification_token",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_verification_token",
    )

    email_verification_repository.consume_token.return_value = {
        "user_id": "user123",
    }

    user_repository.update_email_verified.return_value.modified_count = 1

    # Act
    result = auth_service.verify_email(request)

    # Assert
    assert result.message == "Email verified successfully."

    auth_service._hash_token.assert_called_once_with("plain_verification_token")

    email_verification_repository.consume_token.assert_called_once_with(
        "hashed_verification_token"
    )

    user_repository.update_email_verified.assert_called_once_with("user123")


def test_verify_email_invalid_token(
    auth_service,
    user_repository,
    email_verification_repository,
    mocker,
):
    # Arrange
    request = VerifyEmailRequest(
        token="invalid_token",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_invalid_token",
    )

    email_verification_repository.consume_token.return_value = None

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.verify_email(request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired verification token."

    user_repository.update_email_verified.assert_not_called()


def test_verify_email_update_failed(
    auth_service,
    user_repository,
    email_verification_repository,
    mocker,
):
    # Arrange
    request = VerifyEmailRequest(
        token="plain_verification_token",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_verification_token",
    )

    email_verification_repository.consume_token.return_value = {
        "user_id": "user123",
    }

    user_repository.update_email_verified.return_value.modified_count = 0

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.verify_email(request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Unable to verify email."

    user_repository.update_email_verified.assert_called_once_with("user123")


# Verify Email
#       │
#       ▼
# Hash verification token
#       │
#       ▼
# Consume verification token
#       │
#       ├── Invalid / Expired ❌
#       │
#       ▼
# Update user email_verified
#       │
#       ├── Update failed ❌
#       │
#       ▼
# Return success ✅
