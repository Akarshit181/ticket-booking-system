from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    app_name = os.getenv("APP_NAME", "Auth_Service")
    mongo_uri = os.getenv("MONGO_URI")
    database_name = os.getenv("DATABASE_NAME")
    collection_users = os.getenv("COLLECTION_USERS")
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm = os.getenv("JWT_ALGORITHM")
    jwt_access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
    jwt_refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS"))
    collection_refresh_tokens = os.getenv("COLLECTION_REFERSH_TOKEN")
    collection_password_reset_tokens = os.getenv("COLLECTION_PASSWORD_RESET_TOKENS")
    password_reset_token_expire_minutes = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES")
    )
    collection_email_verification_tokens = os.getenv(
        "COLLECTION_EMAIL_VERIFICATION_TOKENS"
    )
    email_verification_token_expire_minutes = int(
        os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES")
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


settings = Settings()
