import pytest
from fastapi import HTTPException

from app.models.password_reset_model import ResetPasswordRequest
from app.services import password_service


def test_reset_password_success(
    auth_service,
    user_repository,
    password_reset_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = ResetPasswordRequest(
        token="plain_reset_token",
        new_password="NewPassword@123",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_reset_token",
    )

    password_reset_repository.consume_token.return_value = {
        "user_id": "user123",
    }

    mock_hash = mocker.patch.object(
        password_service,
        "hash_password",
        return_value="new_hashed_password",
    )

    # Act
    result = auth_service.reset_password(request)

    # Assert
    assert result.message == "Password reset successfully. Please login again."

    auth_service._hash_token.assert_called_once_with("plain_reset_token")

    password_reset_repository.consume_token.assert_called_once_with(
        "hashed_reset_token"
    )

    mock_hash.assert_called_once_with("NewPassword@123")

    user_repository.update_password.assert_called_once_with(
        "user123",
        "new_hashed_password",
    )

    refresh_token_repository.delete_all_by_user_id.assert_called_once_with("user123")


def test_reset_password_invalid_token(
    auth_service,
    user_repository,
    password_reset_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = ResetPasswordRequest(
        token="invalid_token",
        new_password="NewPassword@123",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_invalid_token",
    )

    password_reset_repository.consume_token.return_value = None

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.reset_password(request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired reset token."

    user_repository.update_password.assert_not_called()

    refresh_token_repository.delete_all_by_user_id.assert_not_called()


# Reset Password
#         │
#         ▼
# Hash reset token
#         │
#         ▼
# Consume reset token
#         │
#         ├── Invalid / Expired ❌
#         │
#         ▼
# Hash new password
#         │
#         ▼
# Update user password
#         │
#         ▼
# Delete all refresh tokens
#         │
#         ▼
# Return success ✅
