from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    app_name = os.getenv("APP_NAME", "Notification_Service")

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL")
    smtp_from_name = os.getenv("SMTP_FROM_NAME")

    log_level = os.getenv("LOG_LEVEL", "INFO")

    cors_allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "",
        ).split(",")
        if origin.strip()
    ]

    def validate(self):
        required_settings = {
            "SMTP_HOST": self.smtp_host,
            "SMTP_USERNAME": self.smtp_username,
            "SMTP_PASSWORD": self.smtp_password,
            "SMTP_FROM_EMAIL": self.smtp_from_email,
            "CORS_ALLOWED_ORIGINS": self.cors_allowed_origins,
        }

        missing_settings = [
            name
            for name, value in required_settings.items()
            if not value
        ]

        if missing_settings:
            raise RuntimeError(
                "Missing required environment variables: "
                + ", ".join(missing_settings)
            )


settings = Settings()

settings.validate()