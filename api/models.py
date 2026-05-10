from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, Boolean, UniqueConstraint
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    link = Column(Text, unique=True, nullable=False)
    category = Column(Text)
    image = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    company = Column(Text)
    location = Column(Text)
    date = Column(Text)



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(Text, unique=True, nullable=False)
    password = Column(Text, nullable=False)

    full_name = Column(Text, nullable=True)
    image = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    username = Column(Text, unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    bio = Column(Text, nullable=True)
    location = Column(Text, nullable=True)


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(Text, default="applied")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    interview_date = Column(DateTime, nullable=True)
    job = relationship("Job")

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="unique_user_job"),
    )