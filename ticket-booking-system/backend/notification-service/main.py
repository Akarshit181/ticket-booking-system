from fastapi import FastAPI
from app.routes.notification import router as notification_router

app = FastAPI(
    title="Notification Service",
    version='1.0.0',
)


@app.get('/')
def root():
    return {
        "message" : "Notification Service Running."
    }
app.include_router(notification_router)