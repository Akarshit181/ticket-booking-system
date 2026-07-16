from jinja2 import TemplateNotFound

from app.models.email_model import EmailRequest
from app.providers.smtp_provider import SMTPProvider
from app.utils.template import template_environment
from app.utils.logger import logger


class NotificationService:

    def __init__(self, smtp_provider: SMTPProvider):
        self.smtp_provider = smtp_provider

    def send_email(self, email_request: EmailRequest):
        try:
            template = template_environment.get_template(
                f"{email_request.template}.html"
            )

            html_body = template.render(**email_request.variables)

        except TemplateNotFound:
            logger.error("Template not found: %s", email_request.template)
            raise ValueError(f"Template '{email_request.template}' not found.")

        self.smtp_provider.send_email(
            recipient=email_request.to,
            subject=email_request.subject,
            html_body=html_body,
        )

        logger.info(
            "Notification email sent to=%s template=%s",
            email_request.to,
            email_request.template,
        )
