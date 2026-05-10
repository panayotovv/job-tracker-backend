from datetime import datetime, timezone
import time
from playwright.sync_api import sync_playwright

CATEGORIES = [
    "back-end-development",
    "front-end-development",
    "full-stack-development",
    "operations",
    "quality-assurance",
    "pm-ba-and-more",
    "data-science",
    "erp-crm-development",
    "mobile-development",
    "ui-ux-and-arts",
    "hardware-and-engineering",
    "customer-support",
    "technical-support",
    "junior-intern",
    "it-management",
]

BASE_URL = "https://dev.bg"


def scrape_category(page, category: str, seen_links: set) -> list[dict]:
    jobs = []
    page_num = 1

    while True:
        url = f"{BASE_URL}/company/jobs/{category}/page/{page_num}"
        print(f"[{category}] Page {page_num} → {url}")
        page.goto(url, wait_until="domcontentloaded")

        try:
            page.wait_for_selector(".job-list-item", timeout=5000)
        except Exception:
            print(f"[{category}] No jobs found → stopping")
            break

        job_cards = page.query_selector_all(".job-list-item")
        if not job_cards:
            break

        new_jobs_found = False

        for job in job_cards:
            try:
                title_el = job.query_selector("h6.job-title, h3.job-title, h6, h3")
                title = title_el.inner_text().strip() if title_el else "No title"

                link_el = job.query_selector("a.overlay-link")
                link = link_el.get_attribute("href") if link_el else None
                if link and link.startswith("/"):
                    link = BASE_URL + link

                if not link or link in seen_links:
                    continue

                seen_links.add(link)
                new_jobs_found = True

                date_el = job.query_selector("span.date.date-with-icon, .date")
                date = date_el.inner_text().strip() if date_el else None

                badges = job.query_selector_all(".tags-wrap .badge")
                location = None
                tags = []

                for badge in badges:
                    text = badge.inner_text().strip()
                    if text:
                        tags.append(text)

                if tags:
                    location = tags[0]

                company_el = job.query_selector(".company-name, .company")
                company = company_el.inner_text().strip() if company_el else None

                img_el = job.query_selector("img")
                image = img_el.get_attribute("src") if img_el else None

                if image and image.startswith("/"):
                    image = BASE_URL + image

                jobs.append({
                    "title": title,
                    "company": company,
                    "date": date,
                    "location": location,
                    "tags": tags,
                    "link": link,
                    "image": image,
                    "category": category,
                })

            except Exception as e:
                print(f"Error parsing job: {e}")
                continue

        if not new_jobs_found:
            break

        page_num += 1
        time.sleep(1)

    return jobs

def scrape_all(headless: bool = True) -> list[dict]:
    all_jobs = []
    seen_links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        for category in CATEGORIES:
            print(f"\nScraping: {category}")
            jobs = scrape_category(page, category, seen_links)
            all_jobs.extend(jobs)

        browser.close()

    print(f"\nTotal jobs scraped: {len(all_jobs)} {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
    return all_jobs




def scrape_latest(existing_links: set, headless: bool = True) -> list[dict]:
    all_jobs = []
    seen_links = set(existing_links)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        for category in CATEGORIES:
            url = f"{BASE_URL}/company/jobs/{category}/page/1"
            print(f"[{category}] Scraping latest → {url}")
            page.goto(url, wait_until="domcontentloaded")

            try:
                page.wait_for_selector(".job-list-item", timeout=5000)
            except Exception:
                continue

            job_cards = page.query_selector_all(".job-list-item")

            for job in job_cards:
                try:
                    link_el = job.query_selector("a.overlay-link")
                    link = link_el.get_attribute("href") if link_el else None
                    if link and link.startswith("/"):
                        link = BASE_URL + link

                    if not link or link in seen_links:
                        continue

                    seen_links.add(link)

                    title_el = job.query_selector("h6.job-title, h3.job-title, h6, h3")
                    title = title_el.inner_text().strip() if title_el else "No title"

                    date_el = job.query_selector("span.date.date-with-icon, .date")
                    date = date_el.inner_text().strip() if date_el else None

                    badges = job.query_selector_all(".tags-wrap .badge")
                    tags = [b.inner_text().strip() for b in badges if b.inner_text().strip()]
                    location = tags[0] if tags else None

                    company_el = job.query_selector(".company-name, .company")
                    company = company_el.inner_text().strip() if company_el else None

                    img_el = job.query_selector("img")
                    image = img_el.get_attribute("src") if img_el else None
                    if image and image.startswith("/"):
                        image = BASE_URL + image

                    all_jobs.append({
                        "title": title,
                        "company": company,
                        "date": date,
                        "location": location,
                        "tags": tags,
                        "link": link,
                        "image": image,
                        "category": category,
                    })

                except Exception as e:
                    print(f"Error parsing job: {e}")
                    continue

        browser.close()

    print(f"New jobs found: {len(all_jobs)}\n")
    return all_jobs
