from app.utils.config import settings

from tests.integration.helpers import (
    register_user,
)


def extract_token(verification_link: str) -> str:
    return verification_link.split("token=")[1]


def test_verify_email_success(
    client,
    test_db,
    mock_notification_client,
):
    payload = register_user(client)

    verification_link = mock_notification_client.last_verification_link

    token = extract_token(verification_link)

    response = client.post(
        "/auth/verify-email",
        json={
            "token": token,
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully."

    user = test_db[settings.collection_users].find_one(
        {
            "email": payload["email"],
        }
    )

    assert user["email_verified"] is True

    verification = test_db[settings.collection_email_verification_tokens].find_one(
        {
            "user_id": str(user["_id"]),
        }
    )

    assert verification["used"] is True


def test_verify_email_invalid_token(client):
    response = client.post(
        "/auth/verify-email",
        json={
            "token": "invalid-token",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification token."


def test_verify_email_token_can_be_used_only_once(
    client,
    mock_notification_client,
):
    payload = register_user(client)

    verification_link = mock_notification_client.last_verification_link

    token = extract_token(verification_link)

    response = client.post(
        "/auth/verify-email",
        json={
            "token": token,
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/auth/verify-email",
        json={
            "token": token,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification token."


def test_verify_email_missing_token(client):
    response = client.post(
        "/auth/verify-email",
        json={},
    )

    assert response.status_code == 422


def test_verify_email_empty_payload(client):
    response = client.post(
        "/auth/verify-email",
        json={},
    )

    assert response.status_code == 422


def test_verify_email_resend_invalidates_old_token(
    client,
    mock_notification_client,
):
    payload = register_user(client)

    first_link = mock_notification_client.last_verification_link

    first_token = extract_token(first_link)

    response = client.post(
        "/auth/resend-verification",
        json={
            "email": payload["email"],
        },
    )

    assert response.status_code == 200

    second_link = mock_notification_client.last_verification_link

    second_token = extract_token(second_link)

    assert first_token != second_token

    response = client.post(
        "/auth/verify-email",
        json={
            "token": first_token,
        },
    )

    assert response.status_code == 400

    response = client.post(
        "/auth/verify-email",
        json={
            "token": second_token,
        },
    )

    assert response.status_code == 200


def test_verify_email_already_verified_user(
    client,
    mock_notification_client,
):
    register_user(client)

    verification_link = mock_notification_client.last_verification_link

    token = extract_token(verification_link)

    response = client.post(
        "/auth/verify-email",
        json={
            "token": token,
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/auth/verify-email",
        json={
            "token": token,
        },
    )

    assert response.status_code == 400


def test_verify_email_login_after_verification(
    client,
    mock_notification_client,
):
    payload = register_user(client)

    response = client.post(
        "/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert response.status_code == 403

    verification_link = mock_notification_client.last_verification_link

    token = extract_token(verification_link)

    response = client.post(
        "/auth/verify-email",
        json={
            "token": token,
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert response.status_code == 200
