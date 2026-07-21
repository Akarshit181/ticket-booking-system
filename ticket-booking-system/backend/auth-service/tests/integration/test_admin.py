from app.services.jwt_service import create_access_token
from app.utils.config import settings

from tests.integration.helpers import (
    register_user,
    verify_email,
    login_user,
)


def create_admin_access_token(user_id, email):
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": "ADMIN",
    }
    return create_access_token(payload)


def test_admin_access_success(client, test_db):
    payload = register_user(client)

    verify_email(
        test_db,
        payload["email"],
    )

    user = test_db[settings.collection_users].find_one(
        {
            "email": payload["email"],
        }
    )

    admin_token = create_admin_access_token(
        user["_id"],
        user["email"],
    )

    response = client.get(
        "/auth/admin",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Welcome Admin"
    assert data["user"] == payload["email"]


def test_admin_user_forbidden(
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
        "/auth/admin",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You do not have permission to perform this action."
    )


def test_admin_without_token(client):
    response = client.get("/auth/admin")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_admin_invalid_token(client):
    response = client.get(
        "/auth/admin",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


def test_admin_refresh_token_not_allowed(
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
        "/auth/admin",
        headers={
            "Authorization": f"Bearer {tokens['refresh_token']}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


def test_admin_malformed_authorization_header(client):
    response = client.get(
        "/auth/admin",
        headers={
            "Authorization": "Invalid token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_admin_empty_bearer_token(client):
    response = client.get(
        "/auth/admin",
        headers={
            "Authorization": "Bearer ",
        },
    )

    assert response.status_code == 401


def test_admin_multiple_requests_same_admin_token(
    client,
    test_db,
):
    payload = register_user(client)

    verify_email(
        test_db,
        payload["email"],
    )

    user = test_db[settings.collection_users].find_one(
        {
            "email": payload["email"],
        }
    )

    admin_token = create_admin_access_token(
        user["_id"],
        user["email"],
    )

    headers = {
        "Authorization": f"Bearer {admin_token}",
    }

    response1 = client.get(
        "/auth/admin",
        headers=headers,
    )

    response2 = client.get(
        "/auth/admin",
        headers=headers,
    )

    assert response1.status_code == 200
    assert response2.status_code == 200
