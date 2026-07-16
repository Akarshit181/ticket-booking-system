from app.providers.smtp_provider import SMTPProvider
from app.services.notification_service import NotificationService


def get_notification_service():
    smtp_provider = SMTPProvider()

    return NotificationService(
        smtp_provider=smtp_provider,
    )