import pytest

from app.utils.config import settings


def register_user(client):
    payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    return payload


def verify_user_email(test_db, email):
    test_db[settings.collection_users].update_one(
        {"email": email},
        {"$set": {"email_verified": True}},
    )


def disable_user(test_db, email):
    test_db[settings.collection_users].update_one(
        {"email": email},
        {"$set": {"is_active": False}},
    )


def login(client, email, password):
    return client.post(
        "/auth/login",
        data={
            "username": email,  # OAuth2PasswordRequestForm uses "username"
            "password": password,
        },
    )


def test_login_success(client, test_db):
    payload = register_user(client)

    verify_user_email(test_db, payload["email"])

    response = login(client, payload["email"], payload["password"])

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"].lower() == "bearer"

    refresh_token = test_db[settings.collection_refresh_tokens].find_one()

    assert refresh_token is not None
    assert refresh_token["user_id"] is not None
    assert refresh_token["token"] is not None


def test_login_invalid_email(client):
    response = login(
        client,
        "unknown@example.com",
        "Password@123",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_invalid_password(client, test_db):
    payload = register_user(client)

    verify_user_email(test_db, payload["email"])

    response = login(
        client,
        payload["email"],
        "WrongPassword@123",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_unverified_email(client):
    payload = register_user(client)

    response = login(
        client,
        payload["email"],
        payload["password"],
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required."


def test_login_disabled_account(client, test_db):
    payload = register_user(client)

    verify_user_email(test_db, payload["email"])
    disable_user(test_db, payload["email"])

    response = login(
        client,
        payload["email"],
        payload["password"],
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is disabled."


def test_login_invalid_email_format(client):
    response = login(
        client,
        "invalid-email",
        "Password@123",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_missing_email(client):
    response = client.post(
        "/auth/login",
        data={
            "password": "Password@123",
        },
    )

    assert response.status_code == 422


def test_login_missing_password(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "john@example.com",
        },
    )

    assert response.status_code == 422


def test_login_empty_form(client):
    response = client.post(
        "/auth/login",
        data={},
    )

    assert response.status_code == 422
