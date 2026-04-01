"""
Analyzes player prop lines against historical data.
"""
import pandas as pd
from data.nfl_data import get_player_stats_vs_opponent, get_player_passing_stats, get_player_rushing_stats
from data.nba_data import get_player_stats_vs_team, get_player_game_log


def analyze_nfl_prop(player_name: str, stat: str, line: float, opponent: str = None) -> dict:
    """
    Analyzes an NFL player prop.
    stat: 'passing_yards', 'rushing_yards', 'touchdowns', 'completions', etc.
    line: the over/under line value
    opponent: optional 3-letter team abbreviation to filter by opponent
    """
    if "pass" in stat.lower() or "yard" in stat.lower() and "rush" not in stat.lower():
        df = get_player_stats_vs_opponent(player_name, opponent, "passing") if opponent else get_player_passing_stats(player_name)
    else:
        df = get_player_stats_vs_opponent(player_name, opponent, "rushing") if opponent else get_player_rushing_stats(player_name)

    if df.empty:
        return {"error": f"No data found for {player_name}", "player": player_name, "stat": stat, "line": line}

    # Map stat name to column
    col_map = {
        "passing_yards": "passing_yards",
        "pass_yards": "passing_yards",
        "rushing_yards": "rushing_yards",
        "rush_yards": "rushing_yards",
        "touchdowns": "touchdowns",
        "tds": "touchdowns",
        "completions": "completions",
        "interceptions": "interceptions",
    }
    col = col_map.get(stat.lower().replace(" ", "_"), stat)

    if col not in df.columns:
        return {"error": f"Stat '{stat}' not found in data", "player": player_name, "stat": stat, "line": line}

    values = df[col].dropna()
    if values.empty:
        return {"error": "No values found", "player": player_name, "stat": stat, "line": line}

    over_count = (values > line).sum()
    under_count = (values <= line).sum()
    total = len(values)
    over_pct = round(over_count / total * 100, 1)

    last_5 = values.tail(5).tolist()
    last_10 = values.tail(10).tolist()

    return {
        "player": player_name,
        "stat": stat,
        "line": line,
        "opponent": opponent,
        "games_analyzed": total,
        "avg": round(values.mean(), 1),
        "median": round(values.median(), 1),
        "over_count": int(over_count),
        "under_count": int(under_count),
        "over_pct": over_pct,
        "last_5_values": last_5,
        "last_10_values": last_10,
        "last_5_avg": round(sum(last_5) / len(last_5), 1) if last_5 else 0,
        "last_10_avg": round(sum(last_10) / len(last_10), 1) if last_10 else 0,
        "trend": _trend(last_10),
    }


def analyze_nba_prop(player_name: str, stat: str, line: float, opponent: str = None) -> dict:
    """
    Analyzes an NBA player prop.
    stat: 'PTS', 'REB', 'AST', 'FG3M', etc.
    """
    if opponent:
        df = get_player_stats_vs_team(player_name, opponent)
    else:
        df = get_player_game_log(player_name)

    if df.empty:
        return {"error": f"No data found for {player_name}", "player": player_name, "stat": stat, "line": line}

    stat_upper = stat.upper()
    if stat_upper not in df.columns:
        # Try common aliases
        aliases = {"POINTS": "PTS", "REBOUNDS": "REB", "ASSISTS": "AST", "THREES": "FG3M", "BLOCKS": "BLK", "STEALS": "STL"}
        stat_upper = aliases.get(stat_upper, stat_upper)

    if stat_upper not in df.columns:
        return {"error": f"Stat '{stat}' not found. Available: {list(df.columns)}", "player": player_name}

    values = df[stat_upper].dropna()
    if values.empty:
        return {"error": "No values found"}

    over_count = (values > line).sum()
    under_count = (values <= line).sum()
    total = len(values)
    over_pct = round(over_count / total * 100, 1)

    last_5 = values.tail(5).tolist()
    last_10 = values.tail(10).tolist()

    return {
        "player": player_name,
        "stat": stat_upper,
        "line": line,
        "opponent": opponent,
        "games_analyzed": total,
        "avg": round(values.mean(), 1),
        "median": round(values.median(), 1),
        "over_count": int(over_count),
        "under_count": int(under_count),
        "over_pct": over_pct,
        "last_5_values": [float(x) for x in last_5],
        "last_10_values": [float(x) for x in last_10],
        "last_5_avg": round(sum(last_5) / len(last_5), 1) if last_5 else 0,
        "last_10_avg": round(sum(last_10) / len(last_10), 1) if last_10 else 0,
        "trend": _trend(last_10),
    }


def _trend(values: list) -> str:
    """Returns 'UP', 'DOWN', or 'FLAT' based on recent values."""
    if len(values) < 4:
        return "INSUFFICIENT DATA"
    first_half = sum(values[: len(values) // 2]) / (len(values) // 2)
    second_half = sum(values[len(values) // 2:]) / (len(values) - len(values) // 2)
    diff = second_half - first_half
    if diff > first_half * 0.05:
        return "UP"
    elif diff < -first_half * 0.05:
        return "DOWN"
    return "FLAT"
