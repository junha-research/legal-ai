# app/routes/auth_test.py


from fastapi import APIRouter, Depends
from app.deps.auth import get_current_user
from app.db.models import User


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/me")

def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "open_id": user.open_id,
        "email": user.email,
        "name": user.name,
        "login_method": user.login_method,
    }
