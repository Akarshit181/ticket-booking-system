# Application startup
#         ↓
# Load configuration
#         ↓
# Required setting missing?
#         │
#         ├── YES → FAIL STARTUP IMMEDIATELY
#         │
#         └── NO  → Start application

# This is called fail-fast configuration validation.
from dotenv import load_dotenv
import os

load_dotenv()


class Settings:

    testing: bool = os.getenv("TESTING", "false").lower() == "true"

    app_name = os.getenv("APP_NAME", "Auth_Service")

    mongo_uri = os.getenv("MONGO_URI")
    database_name = os.getenv("DATABASE_NAME")
    collection_users = os.getenv("COLLECTION_USERS")

    jwt_private_key_path = os.getenv("JWT_PRIVATE_KEY_PATH")

    jwt_public_key_path = os.getenv("JWT_PUBLIC_KEY_PATH")

    jwt_algorithm = os.getenv("JWT_ALGORITHM")

    jwt_access_token_expire_minutes = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    )

    jwt_refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))

    collection_refresh_tokens = os.getenv("COLLECTION_REFRESH_TOKENS")

    collection_password_reset_tokens = os.getenv("COLLECTION_PASSWORD_RESET_TOKENS")

    password_reset_token_expire_minutes = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 15)
    )

    collection_email_verification_tokens = os.getenv(
        "COLLECTION_EMAIL_VERIFICATION_TOKENS"
    )

    email_verification_token_expire_minutes = int(
        os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES", 30)
    )

    redis_host = os.getenv("REDIS_HOST")

    redis_port = int(os.getenv("REDIS_PORT", 6379))

    redis_db = int(os.getenv("REDIS_DB", 0))

    redis_password = os.getenv("REDIS_PASSWORD")

    rate_limit_login = int(os.getenv("RATE_LIMIT_LOGIN", 5))

    rate_limit_register = int(os.getenv("RATE_LIMIT_REGISTER", 3))

    rate_limit_forgot_password = int(os.getenv("RATE_LIMIT_FORGOT_PASSWORD", 3))

    rate_limit_resend_verification = int(os.getenv("RATE_LIMIT_RESEND_VERIFICATION", 3))

    rate_limit_refresh = int(os.getenv("RATE_LIMIT_REFRESH", 20))

    rate_limit_window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))

    login_max_attempts = int(os.getenv("LOGIN_MAX_ATTEMPTS", 5))

    login_attempt_window_seconds = int(os.getenv("LOGIN_ATTEMPT_WINDOW_SECONDS", 300))

    token_bytes = int(os.getenv("TOKEN_BYTES", 32))

    cors_allowed_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

    notification_service_url: str = os.getenv(
        "NOTIFICATION_SERVICE_URL",
        "http://localhost:8001",
    )

    frontend_url: str = os.getenv(
        "FRONTEND_URL",
        "http://localhost:3000",
    )

    def validate(self):
        required_settings = {
            "MONGO_URI": self.mongo_uri,
            "DATABASE_NAME": self.database_name,
            "COLLECTION_USERS": self.collection_users,
            "COLLECTION_REFRESH_TOKENS": (self.collection_refresh_tokens),
            "COLLECTION_PASSWORD_RESET_TOKENS": (self.collection_password_reset_tokens),
            "COLLECTION_EMAIL_VERIFICATION_TOKENS": (
                self.collection_email_verification_tokens
            ),
            "JWT_PRIVATE_KEY_PATH": self.jwt_private_key_path,
            "JWT_PUBLIC_KEY_PATH": self.jwt_public_key_path,
            "JWT_ALGORITHM": self.jwt_algorithm,
            "REDIS_HOST": self.redis_host,
            "CORS_ALLOWED_ORIGINS": self.cors_allowed_origins,
        }

        missing_settings = [
            name for name, value in required_settings.items() if not value
        ]

        if missing_settings:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing_settings)
            )

        allowed_jwt_algorithms = {
            "RS256",
        }

        if self.jwt_algorithm not in allowed_jwt_algorithms:
            raise RuntimeError(
                "JWT_ALGORITHM must be one of: "
                + ", ".join(sorted(allowed_jwt_algorithms))
            )

        if not os.path.isfile(self.jwt_private_key_path):
            raise RuntimeError("JWT private key file does not exist.")

        if not os.path.isfile(self.jwt_public_key_path):
            raise RuntimeError("JWT public key file does not exist.")


settings = Settings()
settings.validate()

# | Feature                                 | Symmetric HS256                      | Asymmetric RS256                |
# | --------------------------------------- | ------------------------------------ | ------------------------------- |
# | Keys                                    | One shared secret                    | Private + public key            |
# | Signing                                 | Secret                               | Private key                     |
# | Verification                            | Same secret                          | Public key                      |
# | Verifier can forge token if key stolen? | Yes                                  | No, not with public key alone   |
# | Setup                                   | Simpler                              | More complex                    |
# | Key distribution                        | Secret must remain secret everywhere | Public key can be distributed   |
# | Single backend                          | Very suitable                        | May be unnecessary              |
# | Microservices                           | Can work                             | Often a better trust model      |
# | Independent token consumers             | Shared signing capability risk       | Verify-only capability          |
# | Key rotation                            | Possible                             | Often cleaner with key IDs/JWKS |
# | Your current service                    | **Yes**                              | No                              |
