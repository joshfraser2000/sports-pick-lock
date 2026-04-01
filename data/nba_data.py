"""
NBA historical stats using nba_api (free, pulls from stats.nba.com).
"""
import pandas as pd
import time
from db.cache import get, set, cache_key
from config import CACHE_TTL_STATS

try:
    from nba_api.stats.endpoints import (
        playergamelog, commonplayerinfo, leaguegamefinder,
        playerdashboardbyopponent, teamgamelog
    )
    from nba_api.stats.static import players, teams
    NBA_AVAILABLE = True
except ImportError:
    NBA_AVAILABLE = False
    print("[NBA] nba_api not installed. Run: pip install nba_api")


def find_player_id(player_name: str) -> int | None:
    if not NBA_AVAILABLE:
        return None
    found = players.find_players_by_full_name(player_name)
    if not found:
        # Try partial match
        all_players = players.get_players()
        found = [p for p in all_players if player_name.lower() in p["full_name"].lower()]
    return found[0]["id"] if found else None


def find_team_id(team_name: str) -> int | None:
    if not NBA_AVAILABLE:
        return None
    all_teams = teams.get_teams()
    matches = [t for t in all_teams if team_name.lower() in t["full_name"].lower()
               or team_name.lower() in t["abbreviation"].lower()
               or team_name.lower() in t["nickname"].lower()]
    return matches[0]["id"] if matches else None


def get_player_game_log(player_name: str, season: str = "2024-25") -> pd.DataFrame:
    if not NBA_AVAILABLE:
        return pd.DataFrame()

    ck = cache_key("nba_gamelog", player_name, season)
    cached = get(ck)
    if cached:
        return pd.DataFrame(cached)

    player_id = find_player_id(player_name)
    if not player_id:
        return pd.DataFrame()

    try:
        time.sleep(0.6)  # respect rate limits
        log = playergamelog.PlayerGameLog(player_id=player_id, season=season)
        df = log.get_data_frames()[0]
        result = df.to_dict("records")
        set(ck, result, CACHE_TTL_STATS)
        return df
    except Exception as e:
        print(f"[NBA] Error fetching game log: {e}")
        return pd.DataFrame()


def get_player_stats_vs_team(player_name: str, opponent_team: str, seasons: list[str] = None) -> pd.DataFrame:
    """Get player stats in games against a specific team across multiple seasons."""
    if seasons is None:
        seasons = ["2022-23", "2023-24", "2024-25"]

    all_games = []
    for season in seasons:
        df = get_player_game_log(player_name, season)
        if df.empty:
            continue
        # MATCHUP column looks like "LAL vs. MIA" or "LAL @ MIA"
        mask = df["MATCHUP"].str.contains(opponent_team, case=False, na=False)
        filtered = df[mask].copy()
        filtered["season"] = season
        all_games.append(filtered)

    if not all_games:
        return pd.DataFrame()

    return pd.concat(all_games, ignore_index=True)


def get_team_h2h(team1: str, team2: str, season: str = "2024-25") -> pd.DataFrame:
    if not NBA_AVAILABLE:
        return pd.DataFrame()

    ck = cache_key("nba_h2h", team1, team2, season)
    cached = get(ck)
    if cached:
        return pd.DataFrame(cached)

    team_id = find_team_id(team1)
    if not team_id:
        return pd.DataFrame()

    try:
        time.sleep(0.6)
        log = teamgamelog.TeamGameLog(team_id=team_id, season=season)
        df = log.get_data_frames()[0]
        h2h = df[df["MATCHUP"].str.contains(team2, case=False, na=False)]
        result = h2h.to_dict("records")
        set(ck, result, CACHE_TTL_STATS)
        return h2h
    except Exception as e:
        print(f"[NBA] Error fetching H2H: {e}")
        return pd.DataFrame()
