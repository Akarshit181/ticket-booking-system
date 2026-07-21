# Imports the main application Class
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.mongodb import MongoDB
from app.database.redis import RedisDB
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.exceptions.handlers import global_exception_handler
from app.middleware.request_id import RequestIDMiddleware
from contextlib import asynccontextmanager
from app.utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    MongoDB.connect()
    RedisDB.connect()

    try:
        yield
    finally:
        RedisDB.close()
        MongoDB.close()


# Use my lifespan() function
#         ↓
# Run startup code
#         ↓
# Run application
#         ↓
# Run shutdown code
app = FastAPI(title="Auth-Service", version="1.0.0", lifespan=lifespan)
# Global exception handler
app.add_exception_handler(
    Exception,
    global_exception_handler,
)


# Suppose your frontend runs on http://localhost:3000 and your api runs on http://localhost:8000.
# The browser considers these different origins and blocks request unless your api allows them.
# allow_origins=["*"] this means allow request from any origin it is good for local but for prodcution restrict it.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)


# This tells take all endpoints insider health_router and register them.
app.include_router(health_router)
app.include_router(auth_router)
