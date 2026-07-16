# A provider is a class that knows how to communicate with an external service.
# SMTP stands for Simple Mail Transfer Protocol.
# This file has only responsibility of sending mail and nothing Single Responsibility Principle (SRP).
# POST /notifications/email
#             │
#             ▼
#       Notification Route
#             │
#             ▼
#    Notification Service
#             │
#             ├── Load Template
#             │
#             ├── Replace Variables
#             │
#             ▼
#       HTML Generated
#             │
#             ▼
#        SMTP Provider
#             │
#             ▼
#       Gmail SMTP Server
#             │
#             ▼
#         User Mailbox
# Why not like mongodb connection because this short lived connections

# smtplib
# Connect
#     ↓
# Login
#     ↓
# Send Email
#     ↓
# Disconnect

import smtplib

# MIMEMultipart
# An email is not just plain text. It containsFrom
# To
# Subject
# Headers

# ↓

# Body

# ↓

# Attachments (optional)
# Think of it like an envelope
from email.mime.multipart import MIMEMultipart

# This is acutal email body . We will mostly send HTML
from email.mime.text import MIMEText

from app.utils.config import settings
from app.utils.logger import logger


class SMTPProvider:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

    def send_email(self, recipient: str, subject: str, html_body: str):
        # Creates an empty email.
        message = MIMEMultipart()
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(
            MIMEText(
                html_body,
                "html",
            )
        )

        try:
            # Creates a connection to:
            # smtp.gmail.com
            #         │
            # Port 587
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.ehlo()
                # Upgrades the connection to TLS encryption.
                # Without this, your username and password would travel unencrypted.
                smtp.starttls()
                print("Connected to:", smtp.sock.getpeername())
                smtp.ehlo()
                print("SMTP Features:", smtp.esmtp_features)
                print("Supports AUTH:", smtp.has_extn("auth"))
                # Authenticate using username and password.
                smtp.login(
                    self.smtp_username,
                    self.smtp_password,
                )
                # Actually sends the MIME email we built.
                smtp.send_message(message)
                # Python automatically calls:
                # smtp.quit() we don't have to do it manually
                logger.info(
                    "Email sent successfully to=%s subject=%s",
                    recipient,
                    subject,
                )

        except Exception:
            logger.exception(
                "Failed to send email to=%s subject=%s",
                recipient,
                subject,
            )
            raise


# ┌────────────────────────────────────┐
# │ From: Ticket Booking System        │
# │       <noreply@example.com>        │
# │                                    │
# │ To: john@gmail.com                 │
# │                                    │
# │ Subject: Verify Email              │
# │                                    │
# │ ---------------------------------  │
# │                                    │
# │ <h2>Hello John</h2>                │
# │                                    │
# │ Click below...                     │
# │                                    │
# └────────────────────────────────────┘
