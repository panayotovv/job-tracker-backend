from pydantic import BaseModel, EmailStr, computed_field
from datetime import datetime
from typing import Optional

months_bg = [
    "яну.", "фев.", "мар.", "апр.", "май", "юни",
    "юли", "авг.", "сеп.", "окт.", "ное.", "дек."
]

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: Optional[int] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    username: Optional[str] = None
    image: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    username: str | None = None
    email: str | None = None
    location: str | None = None
    bio: str | None = None

class JobResponse(BaseModel):
    id: int
    title: str
    link: str
    category: Optional[str]
    image: Optional[str]
    company: Optional[str]
    location: Optional[str]
    date: Optional[str]
    applied: bool = False

    @computed_field
    @property
    def date_display(self) -> Optional[str]:
        if not self.date:
            return None

        d = datetime.strptime(self.date, "%Y-%m-%d")
        return f"{d.day} {months_bg[d.month - 1]}"

    model_config = {
        "from_attributes": True
    }

class PaginatedJobs(BaseModel):
    jobs: list[JobResponse]
    total: int

    model_config = {
        "from_attributes": True
    }


class ApplicationCreate(BaseModel):
    job_id: int
    status: Optional[str] = "Applied"
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    status: Optional[str]
    notes: Optional[str]
    created_at: datetime
    interview_date: Optional[datetime] = None

    job: JobResponse

    model_config = {
        "from_attributes": True
    }


class StatusUpdate(BaseModel):
    status: Optional[str] = None
    interview_date: Optional[datetime] = None