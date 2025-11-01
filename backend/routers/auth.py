from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import users_collection
from backend.models.user import UserCreate, UserOut, Token
from backend.utils.security import hash_password, verify_password, create_access_token
from bson.objectid import ObjectId
from datetime import datetime, timezone

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    # Check if user exists
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    # Hash password
    hashed = hash_password(user.password)

    # Prepare user doc
    user_doc = {
        "email": user.email,
        "hashed_password": hashed,
        "created_at": datetime.now(timezone.utc),
    }

    result = await users_collection.insert_one(user_doc)

    # Build returned user
    created_user = {
        "_id": str(result.inserted_id),
        "email": user.email,
        "created_at": user_doc["created_at"],
    }

    return created_user




@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm uses `username` field; we treat it as email
    user_doc = await users_collection.find_one({"email": form_data.username})
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not user_doc:
        raise error

    if not verify_password(form_data.password, user_doc.get("hashed_password", "")):
        raise error

    access_token = create_access_token({"sub": user_doc["email"]})

    return {"access_token": access_token, "token_type": "bearer"}
