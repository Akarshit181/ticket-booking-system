from app.utils.config import settings

from tests.integration.helpers import (
    register_user,
    verify_email,
    login_user,
    hash_token,
)


def test_logout_success(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    refresh_token = login["refresh_token"]

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully."

    token = test_db[settings.collection_refresh_tokens].find_one(
        {"token": hash_token(refresh_token)}
    )

    assert token is not None
    assert token["is_revoked"] is True
    assert token["revocation_reason"] == "logout"


def test_logout_invalid_token(client):
    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token."


def test_logout_missing_token(client):
    response = client.post(
        "/auth/logout",
        json={},
    )

    assert response.status_code == 422


def test_logout_invalid_payload(client):
    response = client.post(
        "/auth/logout",
        json={
            "token": "abc",
        },
    )

    assert response.status_code == 422


def test_logout_malformed_jwt(client):
    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "abc.def.ghi",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token."


def test_logout_twice(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    refresh_token = login["refresh_token"]

    response = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200

    response = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
    )

    # Your implementation is idempotent
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully."


def test_logout_marks_token_revoked(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    refresh_token = login["refresh_token"]

    client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    token = test_db[settings.collection_refresh_tokens].find_one(
        {
            "token": hash_token(refresh_token),
        }
    )

    assert token is not None
    assert token["is_revoked"] is True
    assert token["revocation_reason"] == "logout"


def test_refresh_after_logout_fails(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    refresh_token = login["refresh_token"]

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token."
