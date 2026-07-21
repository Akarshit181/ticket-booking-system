from tests.integration.helpers import (
    register_user,
    verify_email,
    login_user,
)


def test_me_success(
    client,
    test_db,
):
    payload = register_user(client)

    verify_email(
        test_db,
        payload["email"],
    )

    tokens = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == payload["email"]
    assert data["role"] == "USER"
    assert data["type"] == "access"
    assert "sub" in data
    assert "exp" in data


def test_me_without_authorization_header(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


def test_me_refresh_token_not_allowed(
    client,
    test_db,
):
    payload = register_user(client)

    verify_email(
        test_db,
        payload["email"],
    )

    tokens = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {tokens['refresh_token']}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


def test_me_malformed_authorization_header(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Invalid token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_empty_bearer_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer ",
        },
    )

    assert response.status_code == 401


def test_me_random_jwt_string(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": ("Bearer " "eyJhbGciOiJIUzI1NiJ9." "abc.def"),
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


def test_me_multiple_requests_same_access_token(
    client,
    test_db,
):
    payload = register_user(client)

    verify_email(
        test_db,
        payload["email"],
    )

    tokens = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
    }

    response1 = client.get("/auth/me", headers=headers)
    response2 = client.get("/auth/me", headers=headers)

    assert response1.status_code == 200
    assert response2.status_code == 200

    assert response1.json()["email"] == payload["email"]
    assert response2.json()["email"] == payload["email"]
