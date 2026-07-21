from typing import Any

import httpx

from app.utils.config import settings
from app.utils.logger import logger


class NotificationClient:
    def __init__(self):
        self.base_url = settings.notification_service_url.rstrip("/")

    def send_email(
        self,
        recipient: str,
        subject: str,
        template: str,
        variables: dict[str, Any],
    ) -> None:
        payload = {
            "to": recipient,
            "subject": subject,
            "template": template,
            "variables": variables,
        }

        try:
            url = f"{self.base_url}/notifications/email"

            print("URL:", url)
            print("Payload:", payload)

            response = httpx.post(
                url,
                json=payload,
                timeout=30,
            )

            print("Status:", response.status_code)
            print("Response:", response.text)

            response.raise_for_status()

        except Exception:
            raise

        except httpx.HTTPError:
            logger.exception(
                "Failed to send notification to=%s",
                recipient,
            )
            raise

    def send_verification_email(
        self,
        recipient: str,
        name: str,
        verification_link: str,
    ) -> None:
        self.send_email(
            recipient=recipient,
            subject="Verify your email",
            template="verify_email",
            variables={
                "name": name,
                "verification_link": verification_link,
            },
        )

    def send_password_reset_email(
        self,
        recipient: str,
        name: str,
        reset_link: str,
    ) -> None:
        self.send_email(
            recipient=recipient,
            subject="Reset your password",
            template="reset_password",
            variables={
                "name": name,
                "reset_link": reset_link,
            },
        )
