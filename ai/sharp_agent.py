"""
The Sharp — AI betting agent powered by Groq (free).
Uses Llama 3.3 70B with tool calling to pull live historical data mid-conversation.
Get your free key at https://console.groq.com
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
    print("[Sharp] groq not installed. Run: pip install groq")

# ── Personality ────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are "The Sharp" — a seasoned sports betting analyst with 15 years of experience
beating Vegas lines. You talk like a sharp bettor: direct, confident, occasionally blunt.
You use real betting language naturally: fade the public, sharp money, trap game, juice,
line movement, ATS, steam move, reverse line movement, key numbers, buying points, closing line value.

Your job is to debate picks with users. When someone brings you a line:
1. ALWAYS use your tools to pull the actual historical data first before giving a verdict
2. Be honest — if the data doesn't support a play, say so. Don't just tell people what they want to hear
3. Push back when you see a bad bet. "That line looks like a public trap to me."
4. Get excited when you spot a genuine edge. "Now THAT'S interesting — look at these numbers."
5. Ask follow-up questions: injury reports, line movement, why they like it
6. Reference line value — a pick can be right but at bad odds
7. Keep responses conversational, not robotic. Max 3-4 paragraphs.

When someone is clearly chasing losses or tilting, be real with them.
You're a sharp, not a hype man. Your goal is to help them find ACTUAL edges."""

# ── Tools (OpenAI/Groq format) ─────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_nfl_prop",
            "description": "Look up historical NFL player prop stats. Use for passing yards, rushing yards, touchdowns, completions, interceptions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_name": {"type": "string", "description": "Player name, e.g. 'Dak Prescott'"},
                    "stat": {"type": "string", "description": "passing_yards, rushing_yards, touchdowns, completions, or interceptions"},
                    "line": {"type": "number", "description": "The over/under line value"},
                    "opponent": {"type": "string", "description": "Opponent team abbreviation e.g. 'MIA'. Optional."},
                },
                "required": ["player_name", "stat", "line"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_nba_prop",
            "description": "Look up historical NBA player prop stats. Use for points, rebounds, assists, threes, blocks, steals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_name": {"type": "string", "description": "Player name, e.g. 'LeBron James'"},
                    "stat": {"type": "string", "description": "PTS, REB, AST, FG3M, BLK, or STL"},
                    "line": {"type": "number", "description": "The over/under line value"},
                    "opponent": {"type": "string", "description": "Opponent team name or abbreviation. Optional."},
                },
                "required": ["player_name", "stat", "line"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_nfl_h2h",
            "description": "Get head-to-head history between two NFL teams. Use for spread and total analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team1": {"type": "string", "description": "Team 1 abbreviation, e.g. 'DAL'"},
                    "team2": {"type": "string", "description": "Team 2 abbreviation, e.g. 'NYG'"},
                },
                "required": ["team1", "team2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_prizepicks_lines",
            "description": "Fetch current PrizePicks projections for a sport to see what lines are live right now.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sport": {"type": "string", "description": "NFL, NBA, MLB, or NHL"},
                },
                "required": ["sport"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_confidence",
            "description": "Calculate a confidence score (0-100) for a prop. Call this after getting prop analysis data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_data": {
                        "type": "object",
                        "description": "The analysis dict from analyze_nfl_prop or analyze_nba_prop",
                    },
                },
                "required": ["analysis_data"],
            },
        },
    },
]


# ── Tool execution ─────────────────────────────────────────────────────────────
def _execute_tool(name: str, args: dict) -> str:
    try:
        if name == "analyze_nfl_prop":
            from analysis.prop_analyzer import analyze_nfl_prop
            result = analyze_nfl_prop(args["player_name"], args["stat"], args["line"], args.get("opponent"))
            return json.dumps(result, default=str)

        elif name == "analyze_nba_prop":
            from analysis.prop_analyzer import analyze_nba_prop
            result = analyze_nba_prop(args["player_name"], args["stat"], args["line"], args.get("opponent"))
            return json.dumps(result, default=str)

        elif name == "get_nfl_h2h":
            from analysis.matchup_analyzer import analyze_nfl_h2h
            result = analyze_nfl_h2h(args["team1"], args["team2"])
            return json.dumps(result, default=str)

        elif name == "get_prizepicks_lines":
            from data.prizepicks_fetcher import get_projections
            lines = get_projections(args["sport"])
            return json.dumps(lines[:20], default=str)

        elif name == "score_confidence":
            from analysis.confidence_scorer import score_prop
            result = score_prop(args["analysis_data"])
            return json.dumps(result, default=str)

        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Main agent loop ────────────────────────────────────────────────────────────
def chat(messages: list[dict], sport: str = "NFL") -> tuple[str, list[dict]]:
    """
    Send messages to The Sharp and get a response.
    Returns (response_text, updated_messages).
    messages: list of {"role": "user"/"assistant"/"tool", "content": "..."}
    """
    if not GROQ_AVAILABLE:
        return (
            "I need a GROQ_API_KEY to operate. Get one free at console.groq.com — no credit card needed.",
            messages,
        )

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(messages)

    # Agentic loop — keep going until no more tool calls
    for _ in range(6):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=api_messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
            temperature=0.7,
        )

        msg = response.choices[0].message
        finish = response.choices[0].finish_reason

        # Append assistant message to history
        api_messages.append({
            "role": "assistant",
            "content": msg.content or "",
            **({"tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]} if msg.tool_calls else {}),
        })

        # No tool calls — final answer
        if finish == "stop" or not msg.tool_calls:
            text = msg.content or "No response generated."
            # Return messages without the system prompt prepended
            return text, [m for m in api_messages if m.get("role") != "system"]

        # Execute tool calls
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}
            result = _execute_tool(tc.function.name, args)
            api_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    # Fallback if we hit max iterations
    return "Took too long to pull the data — try again.", [m for m in api_messages if m.get("role") != "system"]


def get_quick_take(line_description: str, sport: str = "NFL") -> str:
    """One-shot quick take on a line. Used by Line Analyzer and Player Props pages."""
    messages = [{"role": "user", "content": f"Quick take on this line: {line_description}. Sport: {sport}"}]
    text, _ = chat(messages, sport)
    return text
