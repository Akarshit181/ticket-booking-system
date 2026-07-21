import pytest

from app.utils.config import settings


def test_register_user_success(client, test_db):
    payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201

    body = response.json()

    # Verify response
    assert body["message"] == "User registered successfully."

    # Verify user saved in database
    user = test_db[settings.collection_users].find_one({"email": payload["email"]})

    assert user is not None
    assert user["username"] == payload["username"]
    assert user["email"] == payload["email"]

    # Password should never be stored in plain text
    assert user["password_hash"] != payload["password"]

    # Email should not be verified immediately
    assert user["email_verified"] is False

    # Verification token should be created
    verification_token = test_db[
        settings.collection_email_verification_tokens
    ].find_one({"user_id": str(user["_id"])})

    assert verification_token is not None
    assert verification_token["token"] is not None
    assert verification_token["user_id"] == str(user["_id"])


def test_register_duplicate_email(client):
    # First user
    payload1 = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload1)
    assert response.status_code == 201

    # Same email, different username
    payload2 = {
        "username": "jane_doe",
        "email": "john@example.com",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload2)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists."


def test_register_duplicate_username(client):
    # First user
    payload1 = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload1)
    assert response.status_code == 201

    # Same username, different email
    payload2 = {
        "username": "john_doe",
        "email": "jane@example.com",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload2)

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already exists."


def test_register_invalid_email(client):
    payload = {
        "username": "john",
        "email": "invalid-email",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_weak_password(client):
    payload = {
        "username": "john",
        "email": "john@example.com",
        "password": "123",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_missing_username(client):
    payload = {
        "email": "john@example.com",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_missing_email(client):
    payload = {
        "username": "john_doe",
        "password": "Password@123",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_missing_password(client):
    payload = {
        "username": "john_doe",
        "email": "john@example.com",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_empty_payload(client):
    response = client.post("/auth/register", json={})

    assert response.status_code == 422
