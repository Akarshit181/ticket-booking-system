from pydantic import BaseModel, EmailStr
from typing import Dict, Any

class EmailRequest(BaseModel):
    to : EmailStr
    subject : str
    template : str
    # We don't know what variables every template will require.
    variables : Dict[str, Any]
    