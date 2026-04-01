"""
UFC stats by scraping ufcstats.com (free, no key needed).
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from db.cache import get, set, cache_key
from config import CACHE_TTL_STATS

BASE = "http://www.ufcstats.com/statistics"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def _get_soup(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"[UFC] Error fetching {url}: {e}")
        return None


def search_fighter(name: str) -> list[dict]:
    """Search for a fighter by name."""
    ck = cache_key("ufc_fighter_search", name)
    cached = get(ck)
    if cached:
        return cached

    soup = _get_soup(f"{BASE}/fighter-details?action=search&query={name.replace(' ', '+')}")
    if not soup:
        return []

    fighters = []
    for row in soup.select("table.b-statistics__table tbody tr"):
        cols = row.select("td")
        if len(cols) < 3:
            continue
        link = cols[0].find("a")
        if not link:
            continue
        fighters.append({
            "name": link.text.strip(),
            "url": link["href"],
            "nickname": cols[1].text.strip(),
            "record": cols[2].text.strip(),
        })

    set(ck, fighters, CACHE_TTL_STATS)
    return fighters


def get_fighter_stats(fighter_url: str) -> dict:
    """Scrape a fighter's stats page."""
    ck = cache_key("ufc_fighter_stats", fighter_url)
    cached = get(ck)
    if cached:
        return cached

    soup = _get_soup(fighter_url)
    if not soup:
        return {}

    stats = {}
    # Career stats box
    for li in soup.select("ul.b-list__box-list li"):
        text = li.get_text(separator="|").strip()
        if "|" in text:
            key, val = text.split("|", 1)
            stats[key.strip()] = val.strip()

    # Fight history
    fights = []
    for row in soup.select("table.b-flag tbody tr"):
        cols = row.select("td")
        if len(cols) < 6:
            continue
        fights.append({
            "result": cols[0].text.strip(),
            "opponent": cols[1].text.strip(),
            "event": cols[2].text.strip(),
            "method": cols[5].text.strip(),
            "round": cols[6].text.strip() if len(cols) > 6 else "",
        })

    stats["fight_history"] = fights
    set(ck, stats, CACHE_TTL_STATS)
    return stats


def get_fighter_history(fighter_name: str) -> dict:
    """Convenience: search + get stats for a fighter."""
    results = search_fighter(fighter_name)
    if not results:
        return {"error": f"Fighter '{fighter_name}' not found"}
    return get_fighter_stats(results[0]["url"])


def get_upcoming_events() -> list[dict]:
    """Returns upcoming UFC events."""
    ck = cache_key("ufc_upcoming")
    cached = get(ck)
    if cached:
        return cached

    soup = _get_soup(f"{BASE}/events?page=all")
    if not soup:
        return []

    events = []
    for row in soup.select("table.b-statistics__table tbody tr.b-statistics__table-row_type_first"):
        link = row.find("a")
        date_cell = row.find("span", class_="b-statistics__date")
        if link and date_cell:
            events.append({
                "name": link.text.strip(),
                "url": link["href"],
                "date": date_cell.text.strip(),
            })

    set(ck, events, 3600)
    return events
