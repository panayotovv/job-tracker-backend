from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.dialects.postgresql import insert
from api.models import Job, Application
from api.schemas import ApplicationCreate
from sqlalchemy import and_

months = {
    "яну.": 1,
    "фев.": 2,
    "мар.": 3,
    "апр.": 4,
    "май": 5,
    "юни": 6,
    "юли": 7,
    "авг.": 8,
    "сеп.": 9,
    "окт.": 10,
    "ное.": 11,
    "дек.": 12
}

def normalize_for_db(text, year=None):
    if year is None:
        year = date.today().year

    day_str, month_str = text.strip().split()

    day = int(day_str)
    month = months[month_str.lower()]

    return f"{year:04d}-{month:02d}-{day:02d}"

def sync_jobs(db: Session, jobs: list[dict]):
    scraped_links = {job["link"] for job in jobs}

    db.query(Job).filter(Job.link.notin_(scraped_links)).delete(synchronize_session=False)
    db.commit()

    for job in jobs:
        stmt = insert(Job).values(
            title=job["title"],
            link=job["link"],
            category=job["category"],
            image=job["image"],
            company=job["company"],
            location=job["location"],
            date=normalize_for_db(job["date"]),
        ).on_conflict_do_nothing(index_elements=["link"])
        db.execute(stmt)

    db.commit()


def save_jobs(db: Session, jobs: list[dict]):
    for job in jobs:
        stmt = insert(Job).values(
            title=job["title"],
            link=job["link"],
            category=job["category"],
            image=job["image"],
            company=job["company"],
            location=job["location"],
            date=normalize_for_db(job["date"])
        ).on_conflict_do_nothing(index_elements=["link"])
        db.execute(stmt)
    db.commit()


def get_user_applications(db: Session, user_id: int, page: int, limit: int, search: str, sort: str, order: str, status: str):
    query = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .options(joinedload(Application.job))
        .filter(Application.user_id == user_id)
    )

    if status:
        query = query.filter(Application.status == status)


    if search:
        query = query.filter(
            Job.title.ilike(f"%{search}%") |
            Job.company.ilike(f"%{search}%")
        )

    if sort == "date":
        query = query.order_by(Application.created_at.desc() if order == "desc" else Application.created_at.asc())
    elif sort == "company":
        query = query.order_by(Job.company.asc() if order == "asc" else Job.company.desc())
    elif sort == "location":
        if order == "remote":
            query = query.order_by(Job.location.ilike("%remote%").desc())
        else:
            query = query.order_by(Job.location.ilike("%remote%").asc())

    total = query.count()
    applications = query.offset((page - 1) * limit).limit(limit).all()

    return applications, total


def create_application(db: Session, user_id: int, data: ApplicationCreate) -> Application:
    existing = (
        db.query(Application)
        .filter(
            Application.user_id == user_id,
            Application.job_id == data.job_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You have already applied to this job"
        )

    application = Application(
        user_id=user_id,
        job_id=data.job_id,
        status=data.status,
        notes=data.notes,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application