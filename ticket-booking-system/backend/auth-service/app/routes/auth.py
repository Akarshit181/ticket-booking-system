from fastapi import APIRouter, status, Depends
from app.dependencies.auth import get_auth_service
from app.dependencies.rbac import require_roles
from app.services.auth_service import AuthService
from app.models.user_model import UserRegister, UserLogin, ChangePasswordRequest
from app.dependencies.security import get_current_user
from app.models.token_model import TokenPayload
from fastapi.security import OAuth2PasswordRequestForm
from app.models.token_model import (
    RefreshTokenRequest,
    AccessTokenResponse,
    LogoutRequest,
)
from app.models.password_reset_model import ForgotPasswordRequest, ResetPasswordRequest
from app.models.response_model import MessageResponse

# Every endpoint automatically starts with /auth because of the prefix.
# tags are used for grouping endpoints in the documentation. In this case, all endpoints will be grouped under "Authentication". Show it's look much cleaner
router = APIRouter(prefix="/auth", tags=["Authentication"])


# FastAPI sees -- Before calling register(), I need an AuthService with Dependency Injection the route knows how to create auth service and with Depends() the route doesn't know where auth_service comes from. It only knows i need one (This is called inversion of control).
# status_code=status.HTTP_201_CREATED , more readable ide autocomplete and return 201 Created
# AuthService → the type of the object you receive (Type Annotation).
# get_auth_service → a function that creates and returns that object.
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserRegister, auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.register_user(user)


# OAuth2PasswordRequestForm extracts the username and password
# from an application/x-www-form-urlencoded request.
# OAuth2 uses the field name "username".
# In our application, the username is actually the user's email.
# Convert the OAuth2 form data into our application's
# UserLogin model so the service layer remains independent
# of FastAPI and OAuth2.
# Pass the UserLogin model to the service layer.
# The service should only contain business logic and should
# not know how the HTTP request was received.
@router.post("/login")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = UserLogin(email=form_data.username, password=form_data.password)
    return auth_service.login_user(user)


@router.get("/me")
async def get_me(current_user: TokenPayload = Depends(get_current_user)):
    return current_user


@router.post("/refresh")
async def refresh_token(
    token_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.refresh_access_token(token_request)


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    logout_request: LogoutRequest, auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.logout(logout_request)


# Why do we inject:
# instead of asking the client to send we get it from JWT as malicious client could send someone else's ID.
@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: TokenPayload = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.change_password(current_user, request)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.forgot_password(request)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest, auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.reset_password(request)


@router.get("/admin")
async def admin_dashboard(
    current_user: TokenPayload = Depends(require_roles("USER")),
):
    return {"message": "Welcome Admin", "user": current_user.email}
