"""
NFL historical stats using nfl_data_py (free, pulls from nflverse GitHub data).
"""
import pandas as pd
from db.cache import get, set, cache_key
from config import CACHE_TTL_STATS

try:
    import nfl_data_py as nfl
    NFL_AVAILABLE = True
except ImportError:
    NFL_AVAILABLE = False
    print("[NFL] nfl_data_py not installed. Run: pip install nfl-data-py")


def get_player_passing_stats(player_name: str, seasons: list[int] = None) -> pd.DataFrame:
    if not NFL_AVAILABLE:
        return pd.DataFrame()

    if seasons is None:
        seasons = list(range(2018, 2025))

    ck = cache_key("nfl_passing", player_name, str(seasons))
    cached = get(ck)
    if cached:
        return pd.DataFrame(cached)

    try:
        pbp = nfl.import_pbp_data(seasons, columns=[
            "game_id", "season", "week", "home_team", "away_team",
            "posteam", "defteam", "passer_player_name", "pass_attempt",
            "complete_pass", "passing_yards", "pass_touchdown", "interception",
            "game_date",
        ])
        df = pbp[pbp["passer_player_name"].str.contains(player_name, case=False, na=False)]
        if df.empty:
            return pd.DataFrame()

        game_stats = df.groupby(["game_id", "season", "week", "posteam", "defteam", "game_date"]).agg(
            attempts=("pass_attempt", "sum"),
            completions=("complete_pass", "sum"),
            passing_yards=("passing_yards", "sum"),
            touchdowns=("pass_touchdown", "sum"),
            interceptions=("interception", "sum"),
        ).reset_index()

        result = game_stats.to_dict("records")
        set(ck, result, CACHE_TTL_STATS)
        return game_stats
    except Exception as e:
        print(f"[NFL] Error fetching passing stats: {e}")
        return pd.DataFrame()


def get_player_rushing_stats(player_name: str, seasons: list[int] = None) -> pd.DataFrame:
    if not NFL_AVAILABLE:
        return pd.DataFrame()

    if seasons is None:
        seasons = list(range(2018, 2025))

    ck = cache_key("nfl_rushing", player_name, str(seasons))
    cached = get(ck)
    if cached:
        return pd.DataFrame(cached)

    try:
        pbp = nfl.import_pbp_data(seasons, columns=[
            "game_id", "season", "week", "home_team", "away_team",
            "posteam", "defteam", "rusher_player_name", "rush_attempt",
            "rushing_yards", "rush_touchdown", "game_date",
        ])
        df = pbp[pbp["rusher_player_name"].str.contains(player_name, case=False, na=False)]
        if df.empty:
            return pd.DataFrame()

        game_stats = df.groupby(["game_id", "season", "week", "posteam", "defteam", "game_date"]).agg(
            carries=("rush_attempt", "sum"),
            rushing_yards=("rushing_yards", "sum"),
            touchdowns=("rush_touchdown", "sum"),
        ).reset_index()

        result = game_stats.to_dict("records")
        set(ck, result, CACHE_TTL_STATS)
        return game_stats
    except Exception as e:
        print(f"[NFL] Error fetching rushing stats: {e}")
        return pd.DataFrame()


def get_team_vs_team(team1: str, team2: str, seasons: list[int] = None) -> pd.DataFrame:
    """Head-to-head game results between two NFL teams."""
    if not NFL_AVAILABLE:
        return pd.DataFrame()

    if seasons is None:
        seasons = list(range(2015, 2025))

    ck = cache_key("nfl_h2h", team1, team2, str(seasons))
    cached = get(ck)
    if cached:
        return pd.DataFrame(cached)

    try:
        schedules = nfl.import_schedules(seasons)
        mask = (
            ((schedules["home_team"] == team1) & (schedules["away_team"] == team2)) |
            ((schedules["home_team"] == team2) & (schedules["away_team"] == team1))
        )
        h2h = schedules[mask].copy()
        if h2h.empty:
            return pd.DataFrame()

        result = h2h[["game_id", "season", "week", "home_team", "away_team",
                       "home_score", "away_score", "gameday", "game_type"]].to_dict("records")
        set(ck, result, CACHE_TTL_STATS)
        return h2h
    except Exception as e:
        print(f"[NFL] Error fetching H2H: {e}")
        return pd.DataFrame()


def get_player_stats_vs_opponent(player_name: str, opponent_team: str, stat_type: str = "passing") -> pd.DataFrame:
    """Get a player's historical stats against a specific opponent."""
    if stat_type == "passing":
        df = get_player_passing_stats(player_name)
    else:
        df = get_player_rushing_stats(player_name)

    if df.empty:
        return pd.DataFrame()

    return df[df["defteam"] == opponent_team].copy()
