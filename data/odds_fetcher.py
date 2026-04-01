"""
Pulls live odds from The Odds API (free tier: 500 req/month).
Get your free key at https://the-odds-api.com
"""
import requests
from config import ODDS_API_KEY, ODDS_API_BASE, SPORT_KEYS, BOOKMAKERS, CACHE_TTL_ODDS
from db.cache import get, set, cache_key


def _get(endpoint: str, params: dict) -> dict | None:
    if not ODDS_API_KEY:
        return None
    try:
        resp = requests.get(f"{ODDS_API_BASE}{endpoint}", params={**params, "apiKey": ODDS_API_KEY}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[OddsAPI] Error: {e}")
        return None


def get_odds(sport: str, markets: str = "h2h,spreads,totals") -> list[dict]:
    """
    Returns list of games with odds for the given sport.
    sport: one of the keys in SPORT_KEYS (e.g. 'NFL')
    """
    sport_key = SPORT_KEYS.get(sport)
    if not sport_key:
        return []

    ck = cache_key("odds", sport_key, markets)
    cached = get(ck)
    if cached is not None:
        return cached

    data = _get(f"/sports/{sport_key}/odds", {
        "regions": "us",
        "markets": markets,
        "bookmakers": ",".join(BOOKMAKERS),
        "oddsFormat": "american",
    })

    if data is None:
        return []

    set(ck, data, CACHE_TTL_ODDS)
    return data


def get_player_props(sport: str, event_id: str) -> list[dict]:
    """Returns player props for a specific event."""
    sport_key = SPORT_KEYS.get(sport)
    if not sport_key:
        return []

    ck = cache_key("props", sport_key, event_id)
    cached = get(ck)
    if cached is not None:
        return cached

    markets = _player_prop_markets(sport)
    data = _get(f"/sports/{sport_key}/events/{event_id}/odds", {
        "regions": "us",
        "markets": markets,
        "bookmakers": "draftkings",
        "oddsFormat": "american",
    })

    if data is None:
        return []

    set(ck, data, CACHE_TTL_ODDS)
    return data


def _player_prop_markets(sport: str) -> str:
    prop_map = {
        "NFL": "player_pass_yds,player_pass_tds,player_rush_yds,player_receptions,player_reception_yds",
        "NBA": "player_points,player_rebounds,player_assists,player_threes",
        "MLB": "batter_hits,batter_home_runs,pitcher_strikeouts",
        "NHL": "player_goals,player_assists,player_shots_on_goal",
    }
    return prop_map.get(sport, "player_points")


def parse_games(raw_odds: list[dict]) -> list[dict]:
    """Flatten raw odds into clean game rows for display."""
    games = []
    for game in raw_odds:
        row = {
            "id": game.get("id"),
            "sport": game.get("sport_key"),
            "home_team": game.get("home_team"),
            "away_team": game.get("away_team"),
            "commence_time": game.get("commence_time"),
            "bookmakers": {},
        }
        for book in game.get("bookmakers", []):
            bk_name = book["key"]
            row["bookmakers"][bk_name] = {}
            for market in book.get("markets", []):
                mk = market["key"]
                row["bookmakers"][bk_name][mk] = market.get("outcomes", [])
        games.append(row)
    return games
