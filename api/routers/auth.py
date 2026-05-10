from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from api.auth import hash_password, verify_password, create_token
from api.models import User
from api.schemas import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="User already exists")

    user = User(username=body.username, email=body.email, password=hash_password(body.password))
    db.add(user)
    db.commit()

    return {"message": "User created"}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()

    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"user_id": user.id})

    return {"access_token": token, "token_type": "bearer"}