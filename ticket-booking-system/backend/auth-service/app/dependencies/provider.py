from app.clients.notification_client import NotificationClient


def get_notification_client() -> NotificationClient:
    return NotificationClient()
