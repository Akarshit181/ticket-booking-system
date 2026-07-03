#Imports the main application Class
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.login import router as login_router
from app.database.mongodb import MongoDB
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router

app = FastAPI(
    title = "Auth-Service",
    version="1.0.0"
)



# Suppose your frontend runs on http://localhost:3000 and your api runs on http://localhost:8000. 
# The browser considers these different origins and blocks request unless your api allows them.
# allow_origins=["*"] this means allow request from any origin it is good for local but for prodcution restrict it.
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#This tells the function will run only on startup not everytime
@app.on_event("startup")
def startup():
    MongoDB.connect()

    print("MongoDB Connected")

#This tells take all endpoints insider health_router and register them.
app.include_router(health_router)
app.include_router(auth_router)

# app.include_router(login_router)