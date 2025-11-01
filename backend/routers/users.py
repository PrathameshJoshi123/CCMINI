from fastapi import APIRouter, Depends
from backend.models.user import UserOut, UserInDB
from backend.utils.security import get_current_user

router = APIRouter()


@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user
