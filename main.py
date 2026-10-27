"""Scrape currently live matches from https://www.diretta.it/live/ and save
per-league CSV files under data/<league>/."""

import os
import re
import csv
import time
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Env settings needed on unix system with wayland issues
os.environ['GDK_BACKEND'] = 'x11'
os.environ['DISABLE_WAYLAND'] = '1'
os.environ['GTK_USE_PORTAL'] = '0'
os.environ['GSETTINGS_BACKEND'] = 'memory'

DIRETTA_IT_BASE_URL = "https://www.diretta.it/live/"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def slugify(name: str) -> str:
    """Turn a league name into a filesystem-safe slug."""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_") or "unknown"


def safe_text(elem) -> str:
    return (elem.text or "").strip() if elem is not None else ""


def get_league_name(league_container) -> str:
    """League display name from the header block inside a .leagues--live."""
    title = league_container.find_elements(By.CLASS_NAME, "headerLeague__title-text")
    if title:
        return safe_text(title[0])
    # Fallback: any element whose class contains "headerLeague" and "title"
    for el in league_container.find_elements(By.CSS_SELECTOR, "[class*='headerLeague']"):
        txt = safe_text(el)
        if txt:
            return txt
    return "Unknown"


def get_match_id(match_row) -> str:
    """Best-effort match id from the row link id attribute or href mid param."""
    link = match_row.find_elements(By.CSS_SELECTOR, "a.eventRowLink")
    if link:
        mid = link[0].get_attribute("id") or ""
        if mid:
            return mid
        href = link[0].get_attribute("href") or ""
        q = parse_qs(urlparse(href).query)
        mids = q.get("mid")
        if mids:
            return mids[0]
    return ""


def parse_match_row(match_row):
    """Extract structured data from a single match row element."""
    home_team = safe_text(
        match_row.find_element(By.CSS_SELECTOR, ".event__homeParticipant .wcl-name_jjfMf")
    )
    away_team = safe_text(
        match_row.find_element(By.CSS_SELECTOR, ".event__awayParticipant .wcl-name_jjfMf")
    )

    home_score_el = match_row.find_elements(By.CSS_SELECTOR, "span.event__score--home")
    away_score_el = match_row.find_elements(By.CSS_SELECTOR, "span.event__score--away")
    home_score = safe_text(home_score_el[0]) if home_score_el else ""
    away_score = safe_text(away_score_el[0]) if away_score_el else ""

    stage_el = match_row.find_elements(By.CSS_SELECTOR, ".event__stage--block")
    stage = safe_text(stage_el[0]) if stage_el else ""

    return {
        "match_id": get_match_id(match_row),
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score,
        "away_score": away_score,
        "status": stage,
    }


def scrape_live_matches():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(DIRETTA_IT_BASE_URL)
        # Wait for the SPA to render the live table
        time.sleep(8)

        leagues = driver.find_elements(By.CSS_SELECTOR, "div.leagues--live")
        results = {}  # league_slug -> list of match dicts

        for league in leagues:
            league_name = get_league_name(league)
            slug = slugify(league_name)
            match_rows = league.find_elements(By.CSS_SELECTOR, "div.event__match.event__match--live")
            matches = [parse_match_row(m) for m in match_rows]
            if matches:
                results[slug] = {"name": league_name, "matches": matches}

        return results
    finally:
        driver.close()


def write_csvs(results):
    for slug, info in results.items():
        league_dir = os.path.join(DATA_DIR, slug)
        os.makedirs(league_dir, exist_ok=True)
        csv_path = os.path.join(league_dir, "matches.csv")
        matches = info["matches"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["match_id", "home_team", "away_team",
                            "home_score", "away_score", "status"],
            )
            writer.writeheader()
            for m in matches:
                writer.writerow(m)
        print(f"[{info['name']}] -> {csv_path} ({len(matches)} matches)")


def main():
    results = scrape_live_matches()
    if not results:
        print("No live matches found.")
        return
    write_csvs(results)
    total = sum(len(v["matches"]) for v in results.values())
    print(f"\nTotal live matches: {total} across {len(results)} leagues.")


if __name__ == "__main__":
    main()