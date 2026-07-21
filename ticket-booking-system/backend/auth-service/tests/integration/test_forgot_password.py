from tests.integration.helpers import (
    register_user,
    verify_email,
)


def test_forgot_password_success(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    response = client.post(
        "/auth/forgot-password",
        json={
            "email": payload["email"],
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Reset link sent to your registered email."

    user = test_db["users"].find_one({"email": payload["email"]})

    token = test_db["password_reset_tokens"].find_one(
        {
            "user_id": str(user["_id"]),
        }
    )

    assert token is not None
    assert token["used"] is False


def test_forgot_password_unknown_email(client):
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": "unknown@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Reset link sent to your registered email."


def test_forgot_password_invalid_email(client):
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": "invalid-email",
        },
    )

    assert response.status_code == 422


def test_forgot_password_missing_email(client):
    response = client.post(
        "/auth/forgot-password",
        json={},
    )

    assert response.status_code == 422


def test_forgot_password_empty_payload(client):
    response = client.post(
        "/auth/forgot-password",
        json={},
    )

    assert response.status_code == 422


def test_forgot_password_revokes_previous_tokens(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    response = client.post(
        "/auth/forgot-password",
        json={
            "email": payload["email"],
        },
    )

    assert response.status_code == 200

    user = test_db["users"].find_one({"email": payload["email"]})

    first_token = test_db["password_reset_tokens"].find_one(
        {
            "user_id": str(user["_id"]),
            "used": False,
        }
    )

    assert first_token is not None

    response = client.post(
        "/auth/forgot-password",
        json={
            "email": payload["email"],
        },
    )

    assert response.status_code == 200

    revoked_token = test_db["password_reset_tokens"].find_one(
        {
            "_id": first_token["_id"],
        }
    )

    assert revoked_token["used"] is True

    active_tokens = list(
        test_db["password_reset_tokens"].find(
            {
                "user_id": str(user["_id"]),
                "used": False,
            }
        )
    )

    assert len(active_tokens) == 1


def test_forgot_password_multiple_requests_keep_only_one_active_token(
    client,
    test_db,
):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    for _ in range(3):
        response = client.post(
            "/auth/forgot-password",
            json={
                "email": payload["email"],
            },
        )

        assert response.status_code == 200

    user = test_db["users"].find_one({"email": payload["email"]})

    active_tokens = list(
        test_db["password_reset_tokens"].find(
            {
                "user_id": str(user["_id"]),
                "used": False,
            }
        )
    )

    assert len(active_tokens) == 1

    used_tokens = list(
        test_db["password_reset_tokens"].find(
            {
                "user_id": str(user["_id"]),
                "used": True,
            }
        )
    )

    assert len(used_tokens) == 2
