from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, case, cast, Date, exists, literal
from api.deps import get_db, get_current_user_optional
from api.schemas import PaginatedJobs
from datetime import date
from api.models import Application, User, Job

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/", response_model=PaginatedJobs)
def get_jobs(
    page: int = 1,
    limit: int = 20,
    search: str = "",
    sort: str = "date",
    order: str = "desc",
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    skip = (page - 1) * limit

    if user:
        applied_subquery = exists().where(
            (Application.user_id == user) &
            (Application.job_id == Job.id)
        )
    else:
        applied_subquery = literal(False)

    query = db.query(Job, applied_subquery.label("applied"))

    if search:
        query = query.filter(
            Job.title.ilike(f"%{search}%") |
            Job.company.ilike(f"%{search}%")
        )

    if sort == "date":
        col = Job.date
        query = query.order_by(desc(col) if order == "desc" else asc(col))

    elif sort == "company":
        col = Job.company
        query = query.order_by(asc(col) if order == "asc" else desc(col))

    elif sort == "location":
        if order == "remote":
            query = query.order_by(
                case(
                    (Job.location.ilike("%remote%"), 0),
                    (Job.location.ilike("%hybrid%"), 1),
                    else_=2
                )
            )
        else:
            query = query.order_by(
                case(
                    (Job.location.ilike("%remote%"), 2),
                    (Job.location.ilike("%hybrid%"), 1),
                    else_=0
                )
            )

    else:
        query = query.order_by(desc(Job.created_at))

    total = db.query(Job).count()
    results = query.offset(skip).limit(limit).all()

    jobs = []
    for job, applied in results:
        job_dict = job.__dict__.copy()
        job_dict["applied"] = applied
        jobs.append(job_dict)

    return {
        "jobs": jobs,
        "total": total
    }

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    try:
        today = date.today()
        total = db.query(Job).count()
        new_today = db.query(Job).filter(cast(Job.date, Date) == today).count()
        return { "total": total, "new_today": new_today }
    except Exception as e:
        print(e)
        raise