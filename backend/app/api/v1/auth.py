from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    user_id: str
    role: str = "PATIENT"  # PATIENT, ATTENDANT, PHYSICIAN, ADMIN
    password: Optional[str] = None

@router.post("/login")
def login(req: LoginRequest):
    return {
        "access_token": f"mock_token_{req.user_id}_{req.role}",
        "token_type": "bearer",
        "user_id": req.user_id,
        "role": req.role
    }
