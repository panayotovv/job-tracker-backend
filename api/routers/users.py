from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_user
from api.models import User, Application, Job
from api.schemas import UserResponse, ApplicationCreate, ApplicationResponse, JobResponse, StatusUpdate, UserUpdate
from api import crud
from sqlalchemy import and_
from datetime import datetime, timedelta
from sqlalchemy import func
from fastapi import UploadFile, File
import os
import shutil
import uuid

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.put("/me", response_model=UserResponse)
def update_me(
    user_update: UserUpdate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = user_update.dict(exclude_unset=True)

    for key, value in data.items():
        if value not in [None, ""]:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user

@router.get("/me/applications")
def get_my_applications(
        page: int = 1,
        limit: int = 20,
        search: str = "",
        sort: str = "date",
        order: str = "desc",
        status: str = "",
        user_id: int = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    applications, total = crud.get_user_applications(db, user_id, page, limit, search, sort, order, status)

    serialized = []
    for a in applications:
        app_data = ApplicationResponse.model_validate(a)
        serialized.append(app_data)

    return {"applications": serialized, "total": total}


@router.post("/me/applications", response_model=ApplicationResponse, status_code=201)
def apply_to_job(
    body: ApplicationCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return crud.create_application(db, user_id, body)

@router.patch("/applications/{application_id}")
def update_application(
    application_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    user: int = Depends(get_current_user),
):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == user
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.status is not None:
        application.status = payload.status
    if payload.interview_date is not None:
        application.interview_date = payload.interview_date

    db.commit()
    db.refresh(application)

    return {
        "status": application.status,
        "interview_date": application.interview_date,
    }


@router.get("/applications/stats")
def get_applications_stats(
        user_id: int = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    base_query = db.query(Application).filter(Application.user_id == user_id)

    applications = base_query.count()

    interviews = base_query.filter(
        Application.status == "Interview scheduled"
    ).count()

    rejected = base_query.filter(
        Application.status == "Rejected"
    ).count()

    offer = base_query.filter(
        Application.status == "Offer received"
    ).count()

    return {
        "applications": applications,
        "interviews": interviews,
        "rejected": rejected,
        "offer": offer
    }

@router.delete("/applications/{application_id}")
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    user: int = Depends(get_current_user),
):
    application = db.query(Application).filter(
        and_(
        Application.id == application_id,
        Application.user_id == user
        )
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(application)
    db.commit()

    return {"message": "Deleted successfully"}

@router.get("/applications/weekly")
def get_weekly_stats(
    db: Session = Depends(get_db),
    user: int = Depends(get_current_user),
):
    today = datetime.utcnow().date()
    start = today - timedelta(weeks=5) - timedelta(days=today.weekday())
    start_dt = datetime.combine(start, datetime.min.time())

    results = (
        db.query(
            func.to_char(Application.created_at, "IYYY-IW").label("year_week"),
            func.count(Application.id).label("count"),
        )
        .filter(
            Application.user_id == user,
            Application.created_at >= start_dt,
        )
        .group_by("year_week")
        .order_by("year_week")
        .all()
    )

    week_map = {row.year_week: row.count for row in results}

    output = []
    for i in range(6):
        week_start = start + timedelta(weeks=i)
        year_week = week_start.strftime("%G-%V")
        output.append({"week": f"Wk {i + 1}", "count": week_map.get(year_week, 0)})

    return output

@router.get("/applications/interviews")
def get_upcoming_interviews(
    db: Session = Depends(get_db),
    user: int = Depends(get_current_user),
):
    now = datetime.utcnow()
    interviews = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Application.user_id == user,
            Application.status == "Interview scheduled",
            Application.interview_date >= now,
        )
        .order_by(Application.interview_date.asc())
        .limit(5)
        .all()
    )
    return [
        {
            "initials": a.job.company[0].upper() if a.job.company else "?",
            "company": a.job.company,
            "role": a.job.title,
            "date": a.interview_date.strftime("%a %d %b"),
            "time": a.interview_date.strftime("%H:%M"),
            "type": "Interview",
        }
        for a in interviews
    ]


@router.post("/avatar")
def change_avatar(
    file: UploadFile = File(...),
    user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == user).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    extension = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"

    file_path = os.path.join("uploads", filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    avatar_url = f"http://localhost:8000/uploads/{filename}"

    db_user.image = avatar_url

    db.commit()
    db.refresh(db_user)

    return {
        "image": avatar_url
    }