from app.database.mongodb import MongoDB
from app.utils.config import settings
from app.models.password_reset_model import PasswordResetDocument
from datetime import datetime, UTC


class PasswordResetRepository:

    def __intit__(self):
        db = MongoDB.get_db()
        self.collection = db[settings.collection_password_reset_tokens]

    def save_reset_token(self, reset_token: PasswordResetDocument):
        document = reset_token.model_dump()
        return self.collection.insert_one(document)

    def find_by_token_hash(self, token: str):
        return self.collection.find_one({"token_hash": token, "used": False})

    def mark_as_used(self, token: str):
        return self.collection.update_one({"token": token}, {"$set": {"used": True}})

    def delete_expired(self):
        return self.collection.delete_many({"expires_at": {"$lt": datetime.now(UTC)}})
