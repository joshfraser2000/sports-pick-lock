"""
Pulls schedules, scores, and team info from ESPN's unofficial API (no key required).
"""
import requests
from db.cache import get, set, cache_key
from config import CACHE_TTL_STATS

BASE = "https://site.api.espn.com/apis/site/v2/sports"

ESPN_SPORT_PATHS = {
    "NFL": "football/nfl",
    "NBA": "basketball/nba",
    "MLB": "baseball/mlb",
    "NHL": "hockey/nhl",
    "UFC/MMA": "mma/ufc",
    "Boxing": "boxing/boxing",
}


def _get(path: str, params: dict = None) -> dict | None:
    try:
        resp = requests.get(f"{BASE}/{path}", params=params or {}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ESPN] Error fetching {path}: {e}")
        return None


def get_scoreboard(sport: str) -> list[dict]:
    """Returns today's games for a sport."""
    path = ESPN_SPORT_PATHS.get(sport)
    if not path:
        return []

    ck = cache_key("espn_scoreboard", sport)
    cached = get(ck)
    if cached:
        return cached

    data = _get(f"{path}/scoreboard")
    if not data:
        return []

    games = []
    for event in data.get("events", []):
        comp = event.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        games.append({
            "id": event.get("id"),
            "name": event.get("name"),
            "date": event.get("date"),
            "status": event.get("status", {}).get("type", {}).get("description", ""),
            "home_team": home.get("team", {}).get("displayName", ""),
            "away_team": away.get("team", {}).get("displayName", ""),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "venue": comp.get("venue", {}).get("fullName", ""),
        })

    set(ck, games, 300)
    return games


def get_team_roster(sport: str, team_abbr: str) -> list[dict]:
    """Returns roster for a team."""
    path = ESPN_SPORT_PATHS.get(sport)
    if not path:
        return []

    ck = cache_key("espn_roster", sport, team_abbr)
    cached = get(ck)
    if cached:
        return cached

    data = _get(f"{path}/teams/{team_abbr}/roster")
    if not data:
        return []

    players = []
    for athlete in data.get("athletes", []):
        for item in athlete.get("items", []):
            players.append({
                "id": item.get("id"),
                "name": item.get("displayName"),
                "position": item.get("position", {}).get("abbreviation", ""),
                "jersey": item.get("jersey", ""),
            })

    set(ck, players, CACHE_TTL_STATS)
    return players


def search_teams(sport: str) -> list[dict]:
    """Returns all teams for a sport."""
    path = ESPN_SPORT_PATHS.get(sport)
    if not path:
        return []

    ck = cache_key("espn_teams", sport)
    cached = get(ck)
    if cached:
        return cached

    data = _get(f"{path}/teams", {"limit": 100})
    if not data:
        return []

    teams = []
    for item in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
        t = item.get("team", {})
        teams.append({
            "id": t.get("id"),
            "name": t.get("displayName"),
            "abbreviation": t.get("abbreviation"),
            "location": t.get("location"),
        })

    set(ck, teams, CACHE_TTL_STATS)
    return teams
