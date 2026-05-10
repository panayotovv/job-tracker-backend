#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.crud import sync_jobs
from api.database import SessionLocal
from scraper.scrape_devbg import scrape_all


def main():
    print("Starting scraper...", flush=True)
    data = scrape_all()

    print(f"Saving {len(data)} jobs to database...")
    db = SessionLocal()
    try:
        sync_jobs(db, data)
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

