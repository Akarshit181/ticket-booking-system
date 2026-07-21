import hashlib

from app.utils.config import settings


def register_user(
    client,
    username="john_doe",
    email="john@example.com",
    password="Password@123",
):
    payload = {
        "username": username,
        "email": email,
        "password": password,
    }

    response = client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    return payload


def verify_email(test_db, email):
    result = test_db[settings.collection_users].update_one(
        {"email": email},
        {
            "$set": {
                "email_verified": True,
            }
        },
    )

    assert result.matched_count == 1


def disable_user(test_db, email):
    result = test_db[settings.collection_users].update_one(
        {"email": email},
        {
            "$set": {
                "is_active": False,
            }
        },
    )

    assert result.matched_count == 1


def enable_user(test_db, email):
    result = test_db[settings.collection_users].update_one(
        {"email": email},
        {
            "$set": {
                "is_active": True,
            }
        },
    )

    assert result.matched_count == 1


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


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_user(test_db, email):
    return test_db[settings.collection_users].find_one({"email": email})


def delete_user(test_db, email):
    test_db[settings.collection_users].delete_one({"email": email})
