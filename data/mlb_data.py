"""
MLB historical stats using pybaseball (free, scrapes Baseball Reference / Statcast).
"""
import pandas as pd
from db.cache import get, set, cache_key
from config import CACHE_TTL_STATS

try:
    import pybaseball as pb
    pb.cache.enable()
    MLB_AVAILABLE = True
except ImportError:
    MLB_AVAILABLE = False
    print("[MLB] pybaseball not installed. Run: pip install pybaseball")


def get_batter_stats(player_name: str, start_year: int = 2020, end_year: int = 2024) -> pd.DataFrame:
    if not MLB_AVAILABLE:
        return pd.DataFrame()

    ck = cache_key("mlb_batter", player_name, start_year, end_year)
    cached = get(ck)
    if cached:
        return pd.DataFrame(cached)

    try:
        # Get batting stats by season
        data = pb.batting_stats(start_year, end_year, qual=1)
        df = data[data["Name"].str.contains(player_name, case=False, na=False)]
        result = df.to_dict("records")
        set(ck, result, CACHE_TTL_STATS)
        return df
    except Exception as e:
        print(f"[MLB] Error fetching batter stats: {e}")
        return pd.DataFrame()


def get_pitcher_stats(player_name: str, start_year: int = 2020, end_year: int = 2024) -> pd.DataFrame:
    if not MLB_AVAILABLE:
        return pd.DataFrame()

    ck = cache_key("mlb_pitcher", player_name, start_year, end_year)
    cached = get(ck)
    if cached:
        return pd.DataFrame(cached)

    try:
        data = pb.pitching_stats(start_year, end_year, qual=1)
        df = data[data["Name"].str.contains(player_name, case=False, na=False)]
        result = df.to_dict("records")
        set(ck, result, CACHE_TTL_STATS)
        return df
    except Exception as e:
        print(f"[MLB] Error fetching pitcher stats: {e}")
        return pd.DataFrame()


def get_statcast_batter(player_name: str, start_dt: str = "2024-04-01", end_dt: str = "2024-10-01") -> pd.DataFrame:
    """
    Returns Statcast data for a batter. Useful for exit velocity, launch angle, etc.
    Dates format: YYYY-MM-DD
    """
    if not MLB_AVAILABLE:
        return pd.DataFrame()

    ck = cache_key("mlb_statcast_batter", player_name, start_dt, end_dt)
    cached = get(ck)
    if cached:
        return pd.DataFrame(cached)

    try:
        # First look up player ID
        player_search = pb.playerid_lookup(player_name.split()[-1], player_name.split()[0])
        if player_search.empty:
            return pd.DataFrame()
        player_id = int(player_search.iloc[0]["key_mlbam"])
        data = pb.statcast_batter(start_dt, end_dt, player_id=player_id)
        result = data.to_dict("records")
        set(ck, result, CACHE_TTL_STATS)
        return data
    except Exception as e:
        print(f"[MLB] Error fetching Statcast: {e}")
        return pd.DataFrame()
