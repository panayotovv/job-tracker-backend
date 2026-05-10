from fastapi import Depends
from fastapi.security import HTTPBearer
from api.database import SessionLocal
from api.auth import decode_token
from fastapi import HTTPException, status
from typing import Optional

security = HTTPBearer(auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token=Depends(security)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user_id = decode_token(token.credentials)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return user_id


def get_current_user_optional(token=Depends(security)) -> Optional[int]:
    if not token:
        return None

    user_id = decode_token(token.credentials)

    if not user_id:
        return None

    return user_id