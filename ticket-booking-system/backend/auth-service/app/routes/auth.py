from fastapi import APIRouter, status, Depends
from app.dependencies.auth import get_auth_service
from app.services.auth_service import AuthService
from app.models.user_model import UserRegister, UserLogin

# Every endpoint automatically starts with /auth because of the prefix.
# tags are used for grouping endpoints in the documentation. In this case, all endpoints will be grouped under "Authentication". Show it's look much cleaner
router = APIRouter(prefix="/auth", tags=["Authentication"])

# FastAPI sees -- Before calling register(), I need an AuthService with Dependency Injection the route knows how to create auth service and with Depends() the route doesn't know where auth_service comes from. It only knows i need one (This is called inversion of control).
# status_code=status.HTTP_201_CREATED , more readable ide autocomplete and return 201 Created
# AuthService → the type of the object you receive (Type Annotation).
# get_auth_service → a function that creates and returns that object.
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.register_user(user)

@router.post("/login")
async def login_user(user: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.login_user(user)
