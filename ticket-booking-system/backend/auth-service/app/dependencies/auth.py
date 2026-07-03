# This module provides a dependency for the AuthService class. It defines a function get_auth_service that returns an instance of AuthService. This can be used in other parts of the application to access authentication-related functionality.
# Instead of creating an object yourself, you ask FastAPI to provide it when needed.
# Without DI (auth_service = AuthService()) you are saying you will create it with DI (auth_service: AuthService = Depends(get_auth_service)) you are saying you will provide it when needed. This is useful for testing and for decoupling components of your application.
# Nothing special.

# It simply returns an object.

from app.services.auth_service import AuthService

def get_auth_service() -> AuthService:
    return AuthService()    