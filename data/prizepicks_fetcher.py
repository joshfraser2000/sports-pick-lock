"""
Pulls projections from PrizePicks public API (no key required).
"""
import requests
from config import PRIZEPICKS_LEAGUE_IDS, CACHE_TTL_PRIZEPICKS
from db.cache import get, set, cache_key

BASE = "https://api.prizepicks.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://app.prizepicks.com/",
}


def get_projections(sport: str) -> list[dict]:
    """Returns current PrizePicks projections for the given sport."""
    league_id = PRIZEPICKS_LEAGUE_IDS.get(sport)
    if not league_id:
        return []

    ck = cache_key("prizepicks", league_id)
    cached = get(ck)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            f"{BASE}/projections",
            params={"league_id": league_id, "per_page": 250, "single_stat": "true"},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        print(f"[PrizePicks] Error: {e}")
        return []

    projections = _parse(raw)
    set(ck, projections, CACHE_TTL_PRIZEPICKS)
    return projections


def _parse(raw: dict) -> list[dict]:
    """Parse PrizePicks API response into flat rows."""
    data = raw.get("data", [])
    included = raw.get("included", [])

    # Build player lookup from included
    players = {}
    for item in included:
        if item.get("type") == "new_player":
            pid = item["id"]
            attrs = item.get("attributes", {})
            players[pid] = {
                "name": attrs.get("display_name", "Unknown"),
                "team": attrs.get("team", ""),
                "position": attrs.get("position", ""),
                "image_url": attrs.get("image_url", ""),
            }

    rows = []
    for proj in data:
        if proj.get("type") != "projection":
            continue
        attrs = proj.get("attributes", {})
        rel = proj.get("relationships", {})
        player_id = rel.get("new_player", {}).get("data", {}).get("id")
        player = players.get(player_id, {})

        rows.append({
            "id": proj["id"],
            "player": player.get("name", "Unknown"),
            "team": player.get("team", ""),
            "position": player.get("position", ""),
            "stat_type": attrs.get("stat_type", ""),
            "line_score": attrs.get("line_score"),
            "description": attrs.get("description", ""),
            "start_time": attrs.get("start_time", ""),
            "status": attrs.get("status", ""),
            "game_id": attrs.get("game_id", ""),
        })

    return rows
