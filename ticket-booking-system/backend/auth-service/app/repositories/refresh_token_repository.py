from app.database.mongodb import MongoDB
from app.utils.config import settings
from app.models.token_model import RefreshTokenDocument
from datetime import datetime, UTC


class RefreshTokenRepository:

    def __init__(self):
        db = MongoDB.get_db()
        self.collection = db[settings.collection_refresh_tokens]

    def save_refresh_token(self, refresh_token: RefreshTokenDocument):
        # MongoDB cannot insert a Pydantic model directly,
        # so model_dump() converts it into a dictionary.
        document = refresh_token.model_dump()
        self.collection.insert_one(document)

    def find_by_token(self, token: str):
        return self.collection.find_one({"token": token})

    def delete_token(self, token: str):
        self.collection.delete_one({"token": token})

    def delete_all_by_user_id(self, user_id: str):
        return self.collection.delete_many({"user_id": user_id})

    def revoke_token(self, token: str, replaced_by_token: str):
        return self.collection.update_one(
            {"token": token},
            {
                "$set": {
                    "is_revoked": True,
                    "revoked_at": datetime.now(UTC),
                    "replaced_by_token": replaced_by_token,
                }
            },
        )

    def revoke_all_by_user_id(self, user_id: str):
        return self.collection.update_many(
            {
                "user_id": user_id,
                "is_revoked": False,
            },
            {
                "$set": {
                    "is_revoked": True,
                    "revoked_at": datetime.now(UTC),
                }
            },
        )

    def consume_for_rotation(
        self,
        token: str,
        replaced_by_token: str,
    ):
        return self.collection.find_one_and_update(
            {
                "token": token,
                "is_revoked": False,
            },
            {
                "$set": {
                    "is_revoked": True,
                    "revoked_at": datetime.now(UTC),
                    "replaced_by_token": replaced_by_token,
                    "revocation_reason": "rotation",
                }
            },
        )

    def revoke_for_logout(self, token: str):
        return self.collection.update_one(
            {
                "token": token,
                "is_revoked": False,
            },
            {
                "$set": {
                    "is_revoked": True,
                    "revoked_at": datetime.now(UTC),
                    "revocation_reason": "logout",
                }
            },
        )
