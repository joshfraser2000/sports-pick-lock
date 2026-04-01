"""
NHL stats using the official NHL API (completely free, no key needed).
Docs: https://gitlab.com/dword4/nhlapi
"""
import requests
import pandas as pd
from db.cache import get, set, cache_key
from config import CACHE_TTL_STATS

BASE = "https://api-web.nhle.com/v1"
BASE_STATS = "https://api.nhle.com/stats/rest/en"


def _get(url: str, params: dict = None) -> dict | None:
    try:
        resp = requests.get(url, params=params or {}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[NHL] Error: {e}")
        return None


def get_schedule(date: str = None) -> list[dict]:
    """Returns today's (or given date) NHL schedule. date: YYYY-MM-DD"""
    url = f"{BASE}/schedule/now" if not date else f"{BASE}/schedule/{date}"
    ck = cache_key("nhl_schedule", date or "today")
    cached = get(ck)
    if cached:
        return cached

    data = _get(url)
    if not data:
        return []

    games = []
    for day in data.get("gameWeek", []):
        for game in day.get("games", []):
            games.append({
                "id": game.get("id"),
                "date": day.get("date"),
                "home_team": game.get("homeTeam", {}).get("commonName", {}).get("default", ""),
                "away_team": game.get("awayTeam", {}).get("commonName", {}).get("default", ""),
                "home_abbrev": game.get("homeTeam", {}).get("abbrev", ""),
                "away_abbrev": game.get("awayTeam", {}).get("abbrev", ""),
                "status": game.get("gameState", ""),
                "home_score": game.get("homeTeam", {}).get("score", 0),
                "away_score": game.get("awayTeam", {}).get("score", 0),
            })

    set(ck, games, 300)
    return games


def get_player_stats(player_name: str, season: str = "20242025") -> dict:
    """Search for a player and return their season stats."""
    ck = cache_key("nhl_player", player_name, season)
    cached = get(ck)
    if cached:
        return cached

    # NHL stats API search
    data = _get(f"{BASE_STATS}/skater/summary", {
        "limit": 50,
        "cayenneExp": f"seasonId={season} and playerName likeIgnoreCase '%25{player_name}%25'",
    })

    if not data or not data.get("data"):
        return {}

    player = data["data"][0]
    result = {
        "name": player.get("skaterFullName"),
        "team": player.get("teamAbbrevs"),
        "position": player.get("positionCode"),
        "games_played": player.get("gamesPlayed"),
        "goals": player.get("goals"),
        "assists": player.get("assists"),
        "points": player.get("points"),
        "plus_minus": player.get("plusMinus"),
        "shots": player.get("shots"),
    }
    set(ck, result, CACHE_TTL_STATS)
    return result


def get_team_h2h(team1_abbrev: str, team2_abbrev: str, season: str = "20242025") -> list[dict]:
    """Returns head-to-head games between two teams in a season."""
    ck = cache_key("nhl_h2h", team1_abbrev, team2_abbrev, season)
    cached = get(ck)
    if cached:
        return cached

    data = _get(f"{BASE}/club-schedule-season/{team1_abbrev}/{season}")
    if not data:
        return []

    games = []
    for game in data.get("games", []):
        home = game.get("homeTeam", {}).get("abbrev", "")
        away = game.get("awayTeam", {}).get("abbrev", "")
        if team2_abbrev in (home, away):
            games.append({
                "date": game.get("gameDate"),
                "home_team": home,
                "away_team": away,
                "home_score": game.get("homeTeam", {}).get("score"),
                "away_score": game.get("awayTeam", {}).get("score"),
                "game_state": game.get("gameState"),
            })

    set(ck, games, CACHE_TTL_STATS)
    return games
