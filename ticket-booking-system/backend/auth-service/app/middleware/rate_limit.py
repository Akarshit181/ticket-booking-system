from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.database.redis import RedisDB

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request : Request, call_next):
        redis_client = RedisDB.get_client()
        response = await call_next(request)
        return response
    