"""
Scores betting lines with a confidence rating (0-100) based on historical data.
Higher = stronger lean toward OVER. Below 50 = lean toward UNDER.
"""


def score_prop(analysis: dict) -> dict:
    """
    Takes output from prop_analyzer and returns a confidence score + label.
    """
    if "error" in analysis:
        return {"score": 50, "label": "NO DATA", "summary": analysis.get("error", "Unknown error")}

    over_pct = analysis.get("over_pct", 50)
    games = analysis.get("games_analyzed", 0)
    last_5_avg = analysis.get("last_5_avg", 0)
    last_10_avg = analysis.get("last_10_avg", 0)
    line = analysis.get("line", 0)
    trend = analysis.get("trend", "FLAT")

    if games < 3:
        return {"score": 50, "label": "INSUFFICIENT DATA", "summary": f"Only {games} games found."}

    # Base score from hit rate
    score = over_pct

    # Adjust for recent trend
    if trend == "UP":
        score += 5
    elif trend == "DOWN":
        score -= 5

    # Adjust if recent avg is significantly above/below line
    if line > 0:
        last5_edge = (last_5_avg - line) / line * 100
        if last5_edge > 10:
            score += 7
        elif last5_edge > 5:
            score += 4
        elif last5_edge < -10:
            score -= 7
        elif last5_edge < -5:
            score -= 4

    # Adjust for sample size confidence
    if games >= 20:
        pass  # full confidence
    elif games >= 10:
        score = 50 + (score - 50) * 0.85
    elif games >= 5:
        score = 50 + (score - 50) * 0.65
    else:
        score = 50 + (score - 50) * 0.4

    score = max(0, min(100, round(score, 1)))

    # Generate label
    if score >= 75:
        label = "STRONG OVER"
    elif score >= 62:
        label = "LEAN OVER"
    elif score >= 55:
        label = "SLIGHT OVER"
    elif score >= 45:
        label = "NEUTRAL"
    elif score >= 38:
        label = "SLIGHT UNDER"
    elif score >= 25:
        label = "LEAN UNDER"
    else:
        label = "STRONG UNDER"

    opponent_note = f" vs {analysis['opponent']}" if analysis.get("opponent") else ""
    summary = (
        f"{analysis['player']} {analysis['stat']} {analysis['line']}{opponent_note}: "
        f"Hit OVER in {analysis['over_count']}/{games} games ({over_pct}%). "
        f"Last 5 avg: {last_5_avg}. Trend: {trend}."
    )

    return {
        "score": score,
        "label": label,
        "summary": summary,
        "over_pct": over_pct,
        "games_analyzed": games,
        "last_5_avg": last_5_avg,
        "trend": trend,
    }


def score_h2h(h2h: dict, bet_on: str, spread: float = 0) -> dict:
    """
    Scores a moneyline or spread bet based on H2H history.
    bet_on: team abbreviation you're betting on
    spread: positive = team is favored by this much; negative = underdog
    """
    if "error" in h2h:
        return {"score": 50, "label": "NO DATA", "summary": h2h.get("error")}

    team1 = h2h.get("team1")
    team2 = h2h.get("team2")
    total_games = h2h.get("total_games", 0)

    if total_games < 2:
        return {"score": 50, "label": "INSUFFICIENT DATA", "summary": "Not enough H2H games."}

    if bet_on == team1:
        win_pct = h2h.get("team1_win_pct", 50)
    elif bet_on == team2:
        win_pct = 100 - h2h.get("team1_win_pct", 50)
    else:
        win_pct = 50

    score = win_pct

    # Sample size adjustment
    if total_games < 5:
        score = 50 + (score - 50) * 0.5

    score = max(0, min(100, round(score, 1)))

    if score >= 65:
        label = "STRONG PICK"
    elif score >= 55:
        label = "LEAN"
    elif score >= 45:
        label = "NEUTRAL"
    else:
        label = "FADE"

    return {
        "score": score,
        "label": label,
        "summary": f"{bet_on} H2H record: {win_pct}% win rate in {total_games} games vs {team1 if bet_on == team2 else team2}.",
        "games_analyzed": total_games,
        "win_pct": win_pct,
    }
