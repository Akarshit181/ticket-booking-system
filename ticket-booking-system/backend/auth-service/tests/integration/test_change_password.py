from app.utils.config import settings

from tests.integration.helpers import (
    register_user,
    verify_email,
    login_user,
    hash_token,
)


def auth_header(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
    }


def test_change_password_success(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    access_token = login["access_token"]
    refresh_token = login["refresh_token"]

    response = client.post(
        "/auth/change-password",
        headers=auth_header(access_token),
        json={
            "old_password": payload["password"],
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "Password changed successfully. Please login again."
    )

    token = test_db[settings.collection_refresh_tokens].find_one(
        {"token": hash_token(refresh_token)}
    )

    assert token is None

    response = client.post(
        "/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."

    response = client.post(
        "/auth/login",
        data={
            "username": payload["email"],
            "password": "NewPassword@123",
        },
    )

    assert response.status_code == 200


def test_change_password_wrong_old_password(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    response = client.post(
        "/auth/change-password",
        headers=auth_header(login["access_token"]),
        json={
            "old_password": "WrongPassword@123",
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Old password is incorrect."


def test_change_password_same_as_old_password(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    response = client.post(
        "/auth/change-password",
        headers=auth_header(login["access_token"]),
        json={
            "old_password": payload["password"],
            "new_password": payload["password"],
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "New password must be different from the old password."
    )


def test_change_password_missing_old_password(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    response = client.post(
        "/auth/change-password",
        headers=auth_header(login["access_token"]),
        json={
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 422


def test_change_password_missing_new_password(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    response = client.post(
        "/auth/change-password",
        headers=auth_header(login["access_token"]),
        json={
            "old_password": payload["password"],
        },
    )

    assert response.status_code == 422


def test_change_password_empty_payload(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    response = client.post(
        "/auth/change-password",
        headers=auth_header(login["access_token"]),
        json={},
    )

    assert response.status_code == 422


def test_change_password_without_access_token(client):
    response = client.post(
        "/auth/change-password",
        json={
            "old_password": "Password@123",
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 401


def test_change_password_invalid_access_token(client):
    response = client.post(
        "/auth/change-password",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "old_password": "Password@123",
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 401


def test_change_password_deleted_user(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    user = test_db[settings.collection_users].find_one({"email": payload["email"]})

    test_db[settings.collection_users].delete_one({"_id": user["_id"]})

    response = client.post(
        "/auth/change-password",
        headers=auth_header(login["access_token"]),
        json={
            "old_password": payload["password"],
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_change_password_invalid_new_password_validation(client, test_db):
    payload = register_user(client)

    verify_email(test_db, payload["email"])

    login = login_user(
        client,
        payload["email"],
        payload["password"],
    )

    response = client.post(
        "/auth/change-password",
        headers=auth_header(login["access_token"]),
        json={
            "old_password": payload["password"],
            "new_password": "abc",
        },
    )

    assert response.status_code == 422
