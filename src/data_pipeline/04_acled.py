"""
ACLED -> real conflict events with dates and coordinates.
Use as a "live event stream" that triggers retasking in your demo.

Needs a free myACLED account (acleddata.com). Set (PowerShell):
  $env:ACLED_EMAIL = "you@example.com"
  $env:ACLED_PASSWORD = "your_password"
Auth follows https://acleddata.com/api-documentation/getting-started
Access level for recent data depends on your account tier.

Usage: python 04_acled.py --countries "India,Pakistan" --start 2024-01-01 --end 2024-12-31
"""
import argparse, getpass, os, sys
import pandas as pd
from common import RAW, session

TOKEN_URL = "https://acleddata.com/oauth/token"
API_URL = "https://acleddata.com/api/acled/read"
FIELDS = ("event_id_cnty|event_date|event_type|sub_event_type|actor1|actor2|"
          "country|admin1|location|latitude|longitude|fatalities|notes")


def get_token(s, email, pw):
    r = s.post(TOKEN_URL, headers={"Content-Type": "application/x-www-form-urlencoded"},
               data={"username": email, "password": pw, "grant_type": "password",
                     "client_id": "acled", "scope": "authenticated"}, timeout=30)
    if r.status_code != 200:
        sys.exit(f"Login failed ({r.status_code}): {r.text[:300]}")
    return r.json()["access_token"]


def country_filter(text: str) -> str:
    # ACLED multi-country syntax: country=India:OR:country=Pakistan
    names = [c.strip() for c in text.replace("|", ",").split(",") if c.strip()]
    return ":OR:country=".join(names)


def main(a):
    email, pw = os.getenv("ACLED_EMAIL"), os.getenv("ACLED_PASSWORD")
    if not (email and pw):
        print("ACLED_EMAIL / ACLED_PASSWORD not set. Enter your ACLED login:")
        email = input("ACLED email: ").strip()
        pw = getpass.getpass("ACLED password (hidden): ")
    if not (email and pw):
        sys.exit("Email and password are required.")
    s = session()
    token = get_token(s, email, pw)
    headers = {"Authorization": f"Bearer {token}"}

    rows, page = [], 1
    while True:
        r = s.get(API_URL, headers=headers, timeout=120, params={
            "_format": "json", "country": country_filter(a.countries),
            "event_date": f"{a.start}|{a.end}", "event_date_where": "BETWEEN",
            "fields": FIELDS, "limit": a.page_size, "page": page})
        if r.status_code != 200:
            sys.exit(f"Data request failed ({r.status_code}): {r.text[:300]}")
        j = r.json()
        data = j.get("data", [])
        if not data:
            if page == 1:
                print("API reply:", str(j)[:300])
            break
        rows += data
        print(f"Page {page}: +{len(data)} (total {len(rows)})")
        if len(data) < a.page_size:
            break
        page += 1
    if not rows:
        print("No rows returned. Check dates, country names and your account's data access.")
        return
    df = pd.DataFrame(rows)
    path = RAW / "acled_events.csv"
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} events -> {path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--countries", default="India", help='e.g. "India,Pakistan"')
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument("--page-size", type=int, default=5000)
    main(p.parse_args())
