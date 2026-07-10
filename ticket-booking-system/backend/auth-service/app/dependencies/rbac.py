# Authorization (What are you allowed to do?)


# What is RBAC
# It's stand for Role Based Access Control) is a method of restricting system access to authorized users based on their specific role within an organization, rather than their individual identity.
#             User Logged In
#                   │
#                   ▼
#            Extract JWT Role
#                   │
#                   ▼
#      Is role allowed for endpoint?
#           │                 │
#          Yes               No
#           │                 │
#           ▼                 ▼
#   Execute Endpoint     403 Forbidden

from fastapi import Depends, HTTPException, status

from app.dependencies.security import get_current_user
from app.models.token_model import TokenPayload

#  * means any nubmer of arguments
# a closure is a nested function that remembers and has access to variables from its outer (enclosing) function’s scope, even after the outer function has finished executing.The Three Rules of a Closure
# To create a closure in Python, you must meet three criteria:

# You must have a nested function (a function inside a function).

# The nested function must refer to a variable defined in the enclosing function.


# The enclosing function must return the nested function.
def require_roles(*allowed_roles: str):

    def role_checker(current_user: TokenPayload = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return role_checker
