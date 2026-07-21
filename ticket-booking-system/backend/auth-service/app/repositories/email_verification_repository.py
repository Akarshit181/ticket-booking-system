from app.database.mongodb import MongoDB
from app.models.email_verification_model import EmailVerificationDocument
from datetime import datetime, UTC
from app.utils.config import settings


class EmailVerificationRepository:
    def __init__(self, db=None):
        self.db = db if db is not None else MongoDB.get_db()
        self.collection = self.db[settings.collection_email_verification_tokens]

    def save_verification_token(
        self,
        verification_token: EmailVerificationDocument,
    ):
        document = verification_token.model_dump()
        return self.collection.insert_one(document)

    def find_by_token_hash(self, token_hash: str):
        return self.collection.find_one(
            {
                "token": token_hash,
                "used": False,
            }
        )

    def mark_as_used(self, token_hash: str):
        return self.collection.update_one(
            {"token": token_hash},
            {"$set": {"used": True}},
        )

    def delete_expired(self):
        return self.collection.delete_many({"expires_at": {"$lt": datetime.now(UTC)}})

    def revoke_all_by_user_id(self, user_id: str):
        return self.collection.update_many(
            {
                "user_id": user_id,
                "used": False,
            },
            {
                "$set": {
                    "used": True,
                    "used_at": datetime.now(UTC),
                }
            },
        )

    def consume_token(self, token_hash: str):
        return self.collection.find_one_and_update(
            {
                "token": token_hash,
                "used": False,
                "expires_at": {"$gt": datetime.now(UTC)},
            },
            {
                "$set": {
                    "used": True,
                    "used_at": datetime.now(UTC),
                }
            },
        )
