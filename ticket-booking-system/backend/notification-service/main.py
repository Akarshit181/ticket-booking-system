from fastapi import FastAPI
from app.routes.notification import router as notification_router
from app.exceptions.handlers import register_exception_handlers

app = FastAPI(
    title="Notification Service",
    version="1.0.0",
)
# Logs full details internally and return clean response
register_exception_handlers(app)


@app.get("/")
def root():
    return {"message": "Notification Service Running."}


app.include_router(notification_router)
