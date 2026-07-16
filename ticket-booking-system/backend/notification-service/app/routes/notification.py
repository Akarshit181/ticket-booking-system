from fastapi import APIRouter, Depends

from app.dependencies.notification import get_notification_service
from app.models.email_model import EmailRequest
from app.models.response_model import MessageResponse
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.post(
    "/email",
    response_model=MessageResponse,
)
def send_email(
    request: EmailRequest,
    notification_service: NotificationService = Depends(
        get_notification_service,
    ),
):
    notification_service.send_email(request)

    return MessageResponse(
        message="Email sent successfully."
    )






# Swagger

#       │

# POST /notifications/email

#       │

#       ▼

# Notification Route

#       │

# Dependency Injection

#       ▼

# NotificationService

#       │

# Render Template

#       ▼

# SMTPProvider

#       │

# smtp.gmail.com

#       │

# Recipient