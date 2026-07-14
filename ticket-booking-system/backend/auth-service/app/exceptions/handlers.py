# Request
#    ↓
# Unhandled Python exception
#    ↓
# global_exception_handler()
#    ├── write traceback to error.log
#    └── return generic 500 response

from fastapi import Request
from fastapi.responses import JSONResponse

from app.utils.logger import logger

# Why use getattr()?
# But suppose the error happens before the request ID middleware sets it, or the middleware configuration changes later. This itself raise Attribute Error

async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    request_id = getattr(
        request.state,
        "request_id",
        "unknown",
    )

    logger.exception(
        "Unhandled exception request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error.",
            "request_id": request_id,
        },
        headers={
            "X-Request-ID": request_id,
        },
    )