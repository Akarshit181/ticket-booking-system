import pytest
from types import SimpleNamespace
from fastapi import HTTPException

from app.models.user_model import ChangePasswordRequest
from app.services import password_service


def test_change_password_success(
    auth_service,
    user_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    current_user = SimpleNamespace(sub="user123")

    request = ChangePasswordRequest(
        old_password="OldPassword@123",
        new_password="NewPassword@123",
    )

    existing_user = {
        "_id": "user123",
        "password_hash": "hashed_password",
    }

    user_repository.get_by_id.return_value = existing_user

    mock_verify = mocker.patch.object(
        password_service,
        "verify_password",
        side_effect=[True, False],
    )

    mock_hash = mocker.patch.object(
        password_service,
        "hash_password",
        return_value="new_hashed_password",
    )

    # Act
    result = auth_service.change_password(
        current_user,
        request,
    )

    # Assert
    assert result.message == ("Password changed successfully. Please login again.")

    user_repository.get_by_id.assert_called_once_with("user123")

    assert mock_verify.call_count == 2

    mock_hash.assert_called_once_with("NewPassword@123")

    user_repository.update_password.assert_called_once_with(
        "user123",
        "new_hashed_password",
    )

    refresh_token_repository.delete_all_by_user_id.assert_called_once_with("user123")


def test_change_password_user_not_found(
    auth_service,
    user_repository,
):
    # Arrange
    current_user = SimpleNamespace(sub="user123")

    request = ChangePasswordRequest(
        old_password="OldPassword@123",
        new_password="NewPassword@123",
    )

    user_repository.get_by_id.return_value = None

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.change_password(
            current_user,
            request,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found."


def test_change_password_old_password_incorrect(
    auth_service,
    user_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    current_user = SimpleNamespace(sub="user123")

    request = ChangePasswordRequest(
        old_password="WrongPassword",
        new_password="NewPassword@123",
    )

    user = {
        "_id": "user123",
        "password_hash": "hashed_password",
    }

    user_repository.get_by_id.return_value = user

    mock_verify = mocker.patch.object(
        password_service,
        "verify_password",
        return_value=False,
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.change_password(
            current_user,
            request,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Old password is incorrect."

    mock_verify.assert_called_once_with(
        "WrongPassword",
        "hashed_password",
    )

    user_repository.update_password.assert_not_called()

    refresh_token_repository.delete_all_by_user_id.assert_not_called()


def test_change_password_new_password_same_as_old(
    auth_service,
    user_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    current_user = SimpleNamespace(sub="user123")

    request = ChangePasswordRequest(
        old_password="OldPassword@123",
        new_password="OldPassword@123",
    )

    user = {
        "_id": "user123",
        "password_hash": "hashed_password",
    }

    user_repository.get_by_id.return_value = user

    mock_verify = mocker.patch.object(
        password_service,
        "verify_password",
        side_effect=[True, True],
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.change_password(
            current_user,
            request,
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail == "New password must be different from the old password."
    )

    assert mock_verify.call_count == 2

    user_repository.update_password.assert_not_called()

    refresh_token_repository.delete_all_by_user_id.assert_not_called()


# Change Password
#        │
#        ▼
# Find User
#        │
#        ├── User not found ❌
#        │
#        ▼
# Verify old password
#        │
#        ├── Incorrect ❌
#        │
#        ▼
# Verify new != old
#        │
#        ├── Same password ❌
#        │
#        ▼
# Hash new password
#        │
#        ▼
# Update password
#        │
#        ▼
# Delete all refresh tokens
#        │
#        ▼
# Return success ✅
