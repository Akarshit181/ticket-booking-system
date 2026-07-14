# ============================================================
# REQUEST ID MIDDLEWARE
# ============================================================
#
# FLOW:
#
# Client Request
#       │
#       ▼
# RequestIDMiddleware
#       │
#       ├── Generate UUID
#       │
#       ▼
# request_id = "550e8400-e29b-41d4-a716-446655440000"
#       │
#       ▼
# Store ID in:
#
# request.state.request_id
#
#       │
#       ▼
# Continue request
#
#       │
#       ▼
# Route / Service / Repository
#
#       │
#       ▼
# Response
#
#       │
#       ▼
# Add response header:
#
# X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
#
#       │
#       ▼
# Client
#
#
# PURPOSE:
#
# One request gets one unique ID.
#
# This ID can later be used to correlate:
#
#   client error
#   API request
#   application logs
#   error logs
#
# ============================================================


import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # Generate a random UUID for this HTTP request.
        request_id = str(uuid.uuid4())

        # Store the request ID on the current request.
        #
        # Later code can access:
        #
        # request.state.request_id
        #
        request.state.request_id = request_id

        # Continue the request through the middleware stack
        # and eventually to the route.
        response = await call_next(request)

        # Return the correlation ID to the client.
        response.headers["X-Request-ID"] = request_id

        return response