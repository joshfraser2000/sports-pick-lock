"""
Simple one-shot line analysis using Groq (free).
Used by Line Analyzer page for a quick verdict without full conversation.
"""
import json
from config import GROQ_API_KEY, GROQ_MODEL

try:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    GROQ_AVAILABLE = bool(GROQ_API_KEY)
except ImportError:
    client = None
    GROQ_AVAILABLE = False


def analyze_line(line_description: str, historical_data: dict, sport: str = "") -> str:
    """
    Takes a line description and historical data, returns a sharp verdict.
    Falls back to rule-based analysis if Groq is unavailable.
    """
    if not GROQ_AVAILABLE:
        return _fallback_analysis(historical_data)

    prompt = f"""Analyze this betting line as a sharp bettor:
LINE: {line_description}
SPORT: {sport}

HISTORICAL DATA:
{json.dumps(historical_data, indent=2, default=str)}

Give a direct verdict in under 150 words. End with: VERDICT: [STRONG OVER / LEAN OVER / NEUTRAL / LEAN UNDER / STRONG UNDER]"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a sharp sports bettor. Be direct, use betting lingo, no fluff."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.6,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq unavailable: {e}\n\n{_fallback_analysis(historical_data)}"


def analyze_natural_language_query(query: str, sport: str = "") -> str:
    """
    Handles a free-form question. Lightweight version — full debate should use sharp_agent.chat().
    """
    if not GROQ_AVAILABLE:
        return "Set your GROQ_API_KEY in .env to enable AI analysis. Get one free at console.groq.com"

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a sharp sports bettor. When given a betting query, give a concise analysis. "
                        "Format: 1) Key factors to consider 2) Your verdict. Under 200 words."
                    ),
                },
                {"role": "user", "content": f"Sport: {sport}\nQuery: {query}"},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq unavailable: {e}"


def _fallback_analysis(data: dict) -> str:
    """Rule-based fallback when AI is unavailable."""
    if "error" in data:
        return f"Could not analyze: {data['error']}"

    over_pct = data.get("over_pct", 50)
    games = data.get("games_analyzed", 0)
    last_5_avg = data.get("last_5_avg", 0)
    line = data.get("line", 0)
    trend = data.get("trend", "FLAT")

    lines = [f"Based on {games} games:"]
    lines.append(f"- Hit OVER {over_pct}% of the time")
    lines.append(f"- Last 5 avg: {last_5_avg} (line: {line})")
    lines.append(f"- Trend: {trend}")

    if over_pct >= 70:
        lines.append("VERDICT: STRONG OVER")
    elif over_pct >= 60:
        lines.append("VERDICT: LEAN OVER")
    elif over_pct <= 30:
        lines.append("VERDICT: STRONG UNDER")
    elif over_pct <= 40:
        lines.append("VERDICT: LEAN UNDER")
    else:
        lines.append("VERDICT: NEUTRAL")

    return "\n".join(lines)
