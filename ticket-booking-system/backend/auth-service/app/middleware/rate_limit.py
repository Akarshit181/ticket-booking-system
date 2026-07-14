# Client

# ↓

# Middleware ⭐

# ↓

# Router

# ↓

# Endpoint

# ↓

# Middleware ⭐

# ↓

# Response

from fastapi import Request
from starlette import status
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.database.redis import RedisDB
from app.utils.config import settings

# The parameter request contain evrything about the HTTP request like request.url, request.method, request.clien.host, request.headers we will use request.client.host
# call_next() This is the next middleware or endpoint.

# Middleware

# ↓

# Endpoint

# ↓

# Response

# ↓

# Back to Middleware

# If you don't call it the endpoint never get execute

# Current Flow

# Receive Request

# ↓

# Get Redis

# ↓

# Execute Endpoint

# ↓

# Return Response
# Difference from RBAC


# RBAC is endpoint-specific:
# Middleware is application-wide:


# How to see the things going in redis
# Open terminal then docker ps the running container then connect with redis cli as docker exec -it redis redis-cli then you can see using key
# KEYS * to see all keys, TTL <key_name> to get Time to live
# INCR + EXPIRE SHOULD BE ATOMIC OPERATION (for redis we will use lua script)
# With lua redis executes the script atomically
# redis.call() , redis.call("INCR", KEYS[1]) it means execute a redis command from inside lua. Lua indexing start from 1 not 0

RATE_LIMITED_ROUTES = {
    ("POST", "/auth/login"): settings.rate_limit_login,
    ("POST", "/auth/register"): settings.rate_limit_register,
    ("POST", "/auth/forgot-password"): settings.rate_limit_forgot_password,
    ("POST", "/auth/resend-verification"): settings.rate_limit_resend_verification,
    ("POST", "/auth/refresh"): settings.rate_limit_refresh,
}

RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

return current
"""


class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        route_key = (request.method, request.url.path)

        limit = RATE_LIMITED_ROUTES.get(route_key)

        if limit is None:
            return await call_next(request)

        redis_client = RedisDB.get_client()

        client_ip = request.client.host

        redis_key = f"rate_limit:{request.method}:{request.url.path}:{client_ip}"

        try: 
            request_count = redis_client.eval(
                RATE_LIMIT_SCRIPT,
                1,
                redis_key,
                settings.rate_limit_window_seconds,
            )
        except Exception as error: 
            print(f"Rate Limiter Redis error: {error}")
            return await call_next(request)

        if request_count > limit:
            ttl = redis_client.ttl(redis_key)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "To many requests. Please try login again."},
                headers={"Retry-After": str(ttl)},
            )

        response = await call_next(request)

        return response
