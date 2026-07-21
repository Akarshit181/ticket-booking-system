from app.utils.config import settings

from tests.integration.helpers import (
    register_user,
    verify_email,
)


def extract_token(verification_link: str) -> str:
    return verification_link.split("token=")[1]


def test_resend_verification_success(
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
    assert response.json() == {
        "message": "If an account with that email exists, a verification email has been sent."
    }

    second_link = mock_notification_client.last_verification_link
    second_token = extract_token(second_link)

    assert second_token != first_token


def test_resend_verification_unknown_email(client):
    response = client.post(
        "/auth/resend-verification",
        json={
            "email": "unknown@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If an account with that email exists, a verification email has been sent."
    }


def test_resend_verification_already_verified(
    client,
    test_db,
):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    response = client.post(
        "/auth/resend-verification",
        json={
            "email": payload["email"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Email is already verified."}


def test_resend_verification_invalid_email(client):
    response = client.post(
        "/auth/resend-verification",
        json={
            "email": "invalid-email",
        },
    )

    assert response.status_code == 422


def test_resend_verification_missing_email(client):
    response = client.post(
        "/auth/resend-verification",
        json={},
    )

    assert response.status_code == 422


def test_resend_verification_empty_payload(client):
    response = client.post(
        "/auth/resend-verification",
        json={},
    )

    assert response.status_code == 422


def test_resend_verification_revokes_previous_tokens(
    client,
    test_db,
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
    assert response.json()["detail"] == "Invalid or expired verification token."

    response = client.post(
        "/auth/verify-email",
        json={
            "token": second_token,
        },
    )

    assert response.status_code == 200

    user = test_db[settings.collection_users].find_one(
        {
            "email": payload["email"],
        }
    )

    assert user["email_verified"] is True


def test_resend_verification_multiple_requests_only_latest_token_works(
    client,
    mock_notification_client,
):
    payload = register_user(client)

    client.post(
        "/auth/resend-verification",
        json={
            "email": payload["email"],
        },
    )

    first_new_link = mock_notification_client.last_verification_link
    first_new_token = extract_token(first_new_link)

    client.post(
        "/auth/resend-verification",
        json={
            "email": payload["email"],
        },
    )

    latest_link = mock_notification_client.last_verification_link
    latest_token = extract_token(latest_link)

    assert first_new_token != latest_token

    response = client.post(
        "/auth/verify-email",
        json={
            "token": first_new_token,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification token."

    response = client.post(
        "/auth/verify-email",
        json={
            "token": latest_token,
        },
    )

    assert response.status_code == 200
