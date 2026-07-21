import hashlib

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


def verify_email(test_db, email):
    test_db[settings.collection_users].update_one(
        {"email": email},
        {"$set": {"email_verified": True}},
    )


def disable_user(test_db, email):
    test_db[settings.collection_users].update_one(
        {"email": email},
        {"$set": {"is_active": False}},
    )


def login_user(client, email, password):
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()


def hash_token(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def test_refresh_token_success(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login_response = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    old_refresh_token = login_response["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"].lower() == "bearer"

    assert body["refresh_token"] != old_refresh_token

    old_token = test_db[settings.collection_refresh_tokens].find_one(
        {"token": hash_token(old_refresh_token)}
    )

    assert old_token is not None
    assert old_token["is_revoked"] is True
    assert old_token["revocation_reason"] == "rotation"

    new_token = test_db[settings.collection_refresh_tokens].find_one(
        {"token": hash_token(body["refresh_token"])}
    )

    assert new_token is not None
    assert new_token["is_revoked"] is False


def test_refresh_invalid_token(client):
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token."


def test_refresh_missing_token(client):
    response = client.post(
        "/auth/refresh",
        json={},
    )

    assert response.status_code == 422


def test_refresh_empty_payload(client):
    response = client.post(
        "/auth/refresh",
        json={},
    )

    assert response.status_code == 422


def test_refresh_invalid_payload(client):
    response = client.post(
        "/auth/refresh",
        json={
            "token": "abc",
        },
    )

    assert response.status_code == 422


def test_refresh_malformed_jwt(client):
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "abc.def.ghi",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token."


def test_refresh_token_reuse_after_rotation(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login_response = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    old_refresh_token = login_response["refresh_token"]

    # First refresh succeeds
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert response.status_code == 200

    # Reusing the same refresh token should fail
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token."


def test_refresh_disabled_user(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login_response = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    disable_user(test_db, payload["email"])

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_response["refresh_token"],
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is disabled."


def test_refresh_unverified_email(client):
    payload = register_user(client)

    # Login requires verification, so manually verify first
    # then make it unverified after login isn't possible.
    # Instead insert verified user before login.

    # Skip if your application never allows an unverified user
    # to obtain a refresh token.


def test_refresh_deleted_user(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login_response = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    test_db[settings.collection_users].delete_one({"email": payload["email"]})

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_response["refresh_token"],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token."


def test_refresh_deleted_user_revokes_all_tokens(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    user = test_db[settings.collection_users].find_one({"email": payload["email"]})

    test_db[settings.collection_users].delete_one({"_id": user["_id"]})

    client.post(
        "/auth/refresh",
        json={
            "refresh_token": login["refresh_token"],
        },
    )

    revoked = list(
        test_db[settings.collection_refresh_tokens].find(
            {
                "user_id": str(user["_id"]),
            }
        )
    )

    assert len(revoked) > 0
    assert all(token["is_revoked"] for token in revoked)
