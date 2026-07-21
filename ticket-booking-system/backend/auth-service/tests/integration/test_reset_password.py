from app.utils.config import settings

from tests.integration.helpers import (
    register_user,
    verify_email,
    login_user,
    hash_token,
)


def extract_token(reset_link: str) -> str:
    return reset_link.split("token=")[1]


def test_reset_password_success(
    client,
    test_db,
    mock_notification_client,
):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    response = client.post(
        "/auth/forgot-password",
        json={
            "email": payload["email"],
        },
    )

    assert response.status_code == 200

    token = extract_token(mock_notification_client.last_reset_link)

    response = client.post(
        "/auth/reset-password",
        json={
            "token": token,
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["message"] == "Password reset successfully. Please login again."
    )

    user = test_db[settings.collection_users].find_one({"email": payload["email"]})

    reset_doc = test_db[settings.collection_password_reset_tokens].find_one(
        {
            "user_id": str(user["_id"]),
            "token": hash_token(token),
        }
    )

    assert reset_doc["used"] is True

    tokens = list(
        test_db[settings.collection_refresh_tokens].find(
            {
                "user_id": str(user["_id"]),
            }
        )
    )

    assert len(tokens) == 0

    response = client.post(
        "/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert response.status_code == 401

    response = client.post(
        "/auth/login",
        data={
            "username": payload["email"],
            "password": "NewPassword@123",
        },
    )

    assert response.status_code == 200


def test_reset_password_invalid_token(client):
    response = client.post(
        "/auth/reset-password",
        json={
            "token": "invalid-token",
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token."


def test_reset_password_token_can_be_used_only_once(
    client,
    test_db,
    mock_notification_client,
):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    client.post(
        "/auth/forgot-password",
        json={
            "email": payload["email"],
        },
    )

    token = extract_token(mock_notification_client.last_reset_link)

    response = client.post(
        "/auth/reset-password",
        json={
            "token": token,
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/auth/reset-password",
        json={
            "token": token,
            "new_password": "AnotherPassword@123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token."


def test_reset_password_missing_token(client):
    response = client.post(
        "/auth/reset-password",
        json={
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 422


def test_reset_password_missing_password(client):
    response = client.post(
        "/auth/reset-password",
        json={
            "token": "abc",
        },
    )

    assert response.status_code == 422


def test_reset_password_empty_payload(client):
    response = client.post(
        "/auth/reset-password",
        json={},
    )

    assert response.status_code == 422


def test_reset_password_invalid_password_validation(client):
    response = client.post(
        "/auth/reset-password",
        json={
            "token": "abc",
            "new_password": "123",
        },
    )

    assert response.status_code == 422


def test_reset_password_multiple_requests_only_latest_token_works(
    client,
    test_db,
    mock_notification_client,
):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    client.post(
        "/auth/forgot-password",
        json={
            "email": payload["email"],
        },
    )

    first_token = extract_token(mock_notification_client.last_reset_link)

    client.post(
        "/auth/forgot-password",
        json={
            "email": payload["email"],
        },
    )

    second_token = extract_token(mock_notification_client.last_reset_link)

    response = client.post(
        "/auth/reset-password",
        json={
            "token": first_token,
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 400

    response = client.post(
        "/auth/reset-password",
        json={
            "token": second_token,
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 200
