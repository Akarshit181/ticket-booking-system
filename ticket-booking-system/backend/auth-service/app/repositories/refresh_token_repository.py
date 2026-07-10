from app.database.mongodb import MongoDB
from app.utils.config import settings
from app.models.token_model import RefreshTokenDocument


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
        return self.collection.find_one({"token": token, "is_revoked": False})

    def delete_token(self, token: str):
        self.collection.delete_one({"token": token})


    def delete_all_by_user_id(self, user_id: str):
        return self.collection.delete_many({"user_id": user_id})
