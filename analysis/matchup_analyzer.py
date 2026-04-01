"""
Analyzes head-to-head matchup history between two teams.
"""
import pandas as pd
from data.nfl_data import get_team_vs_team as nfl_h2h
from data.nba_data import get_team_h2h as nba_h2h
from data.nhl_data import get_team_h2h as nhl_h2h


def analyze_nfl_h2h(team1: str, team2: str, seasons: list[int] = None) -> dict:
    """
    Returns H2H summary for two NFL teams.
    team1/team2: 3-letter abbreviations (e.g. 'DAL', 'GB')
    """
    df = nfl_h2h(team1, team2, seasons)
    if df.empty:
        return {"error": "No H2H data found", "team1": team1, "team2": team2}

    games = []
    team1_wins = 0
    team2_wins = 0
    total_points = []

    for _, row in df.iterrows():
        home = row.get("home_team")
        away = row.get("away_team")
        home_score = row.get("home_score")
        away_score = row.get("away_score")

        if pd.isna(home_score) or pd.isna(away_score):
            continue

        home_score = int(home_score)
        away_score = int(away_score)
        total = home_score + away_score
        total_points.append(total)

        winner = home if home_score > away_score else away
        if winner == team1:
            team1_wins += 1
        else:
            team2_wins += 1

        games.append({
            "season": row.get("season"),
            "week": row.get("week"),
            "home": home,
            "away": away,
            "home_score": home_score,
            "away_score": away_score,
            "total": total,
            "winner": winner,
            "date": row.get("gameday"),
        })

    total_games = team1_wins + team2_wins
    avg_total = sum(total_points) / len(total_points) if total_points else 0
    over_count = sum(1 for t in total_points if t > avg_total)

    return {
        "team1": team1,
        "team2": team2,
        "total_games": total_games,
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "team1_win_pct": round(team1_wins / total_games * 100, 1) if total_games else 0,
        "avg_total_points": round(avg_total, 1),
        "highest_total": max(total_points) if total_points else 0,
        "lowest_total": min(total_points) if total_points else 0,
        "games": games[-10:],  # last 10
    }


def analyze_nba_h2h(team1: str, team2: str, season: str = "2024-25") -> dict:
    df = nba_h2h(team1, team2, season)
    if df.empty:
        return {"error": "No H2H data found", "team1": team1, "team2": team2}

    games = []
    team1_wins = 0
    team2_wins = 0
    totals = []

    for _, row in df.iterrows():
        pts = row.get("PTS", 0)
        matchup = row.get("MATCHUP", "")
        wl = row.get("WL", "")

        # Estimate opponent score from margin if available
        plus_minus = row.get("PLUS_MINUS", 0)
        opp_pts = pts - plus_minus if plus_minus else 0
        total = pts + opp_pts if opp_pts else pts
        totals.append(total)

        if wl == "W":
            team1_wins += 1
        else:
            team2_wins += 1

        games.append({
            "date": row.get("GAME_DATE"),
            "matchup": matchup,
            "pts": pts,
            "opp_pts": opp_pts,
            "total": total,
            "result": wl,
        })

    total_games = team1_wins + team2_wins
    avg_total = sum(totals) / len(totals) if totals else 0

    return {
        "team1": team1,
        "team2": team2,
        "season": season,
        "total_games": total_games,
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "team1_win_pct": round(team1_wins / total_games * 100, 1) if total_games else 0,
        "avg_total_points": round(avg_total, 1),
        "games": games,
    }
