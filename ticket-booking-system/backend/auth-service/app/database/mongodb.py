from pymongo import MongoClient

from app.utils.config import settings

from pymongo import MongoClient

from app.utils.config import settings


class MongoDB:
    client = None
    db = None

    @classmethod
    def connect(cls):
        if cls.client is None:
            cls.client = MongoClient(settings.mongo_uri)
            cls.db = cls.client[settings.database_name]
            print("MongoDB Connected")

    @classmethod
    def get_db(cls):
        return cls.db

    @classmethod
    def close(cls):
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None



# db.users.createIndex(
#     { email: 1 },
#     {
#         unique: true,
#         name: "uq_users_email"
#     }
# )

# db.users.createIndex(
#     { username: 1 },
#     {
#         unique: true,
#         name: "uq_users_username"
#     }
# )
# db.refresh_tokens.createIndex(
#     { token: 1 },
#     {
#         unique: true,
#         name: "uq_refresh_tokens_token"
#     }
# )
# db.refresh_tokens.createIndex(
#     { user_id: 1 },
#     {
#         name: "idx_refresh_tokens_user_id"
#     }
# )
# db.refresh_tokens.createIndex(
#     { expires_at: 1 },
#     {
#         expireAfterSeconds: 0,
#         name: "ttl_refresh_tokens_expires_at"
#     }
# )
# db.email_verification_tokens.createIndex(
#     { token: 1 },
#     {
#         unique: true,
#         name: "uq_email_verification_tokens_token"
#     }
# )
# db.email_verification_tokens.createIndex(
#     { user_id: 1 },
#     {
#         name: "idx_email_verification_tokens_user_id"
#     }
# )
# db.email_verification_tokens.createIndex(
#     { expires_at: 1 },
#     {
#         expireAfterSeconds: 0,
#         name: "ttl_email_verification_tokens_expires_at"
#     }
# )
# db.password_reset_tokens.createIndex(
#     { token: 1 },
#     {
#         unique: true,
#         name: "uq_password_reset_tokens_token"
#     }
# )
# db.password_reset_tokens.createIndex(
#     { user_id: 1 },
#     {
#         name: "idx_password_reset_tokens_user_id"
#     }
# )
# db.password_reset_tokens.createIndex(
#     { expires_at: 1 },
#     {
#         expireAfterSeconds: 0,
#         name: "ttl_password_reset_tokens_expires_at"
#     }
# )




# Auth Service starts
#         ↓
# MongoDB.connect()
#         ↓
# MongoClient created
#         ↓
# Application runs
#         ↓
# Auth Service stops
#         ↓
# MongoDB.close()
#         ↓
# MongoClient.close()
#         ↓
# client = None
# db = None