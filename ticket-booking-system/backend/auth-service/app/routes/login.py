from fastapi import APIRouter
from app.utils.logger import logger
from app.utils.security import create_access_token

router = APIRouter()

@router.post("/login")
def login(data: dict):
    email = data.get("email")
    password = data.get("password")

    logger.info(f"Login attempt for email: {email}")

    try:
        if email == "admin@gmail.com" and password == "123456":
            access_token = create_access_token({
                "sub": email
            })

            logger.info(f"Login success for {email}")

            return {
                "success": True,
                "access_token": access_token,
                "token_type": "bearer"
            }

        logger.warning(f"Invalid login for {email}")

        return {
            "success": False,
            "message": "Invalid credentials"
        }

    except Exception as e:
        logger.error(f"Login error for {email}: {str(e)}")

        return {
            "success": False,
            "message": "Internal server error"
        }