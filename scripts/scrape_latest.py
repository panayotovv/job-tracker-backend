import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.crud import save_jobs
from api.database import SessionLocal
from api.models import Job
from scraper.scrape_devbg import scrape_latest


def run_latest_scrape():
    db = SessionLocal()
    existing_links = {job.link for job in db.query(Job.link).all()}
    db.close()

    print(f"Starting to scrape latest {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
    new_jobs = scrape_latest(existing_links)

    if new_jobs:
        db = SessionLocal()
        save_jobs(db, new_jobs)
        db.commit()
        db.close()
        print(f"Inserted {len(new_jobs)} new jobs")
        print(f"{[job["title"] for job in new_jobs]}\n")

if __name__ == "__main__":
    run_latest_scrape()