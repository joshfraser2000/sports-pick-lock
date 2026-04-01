import os
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Groq model to use (free, fast)
GROQ_MODEL = "llama-3.3-70b-versatile"

# Supabase (free at supabase.com)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")       # Price ID for $30/month
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# App URL (update when deployed)
APP_URL = os.getenv("APP_URL", "http://localhost:8501")

ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# The Odds API sport keys
SPORT_KEYS = {
    "NFL": "americanfootball_nfl",
    "NBA": "basketball_nba",
    "MLB": "baseball_mlb",
    "NHL": "icehockey_nhl",
    "UFC/MMA": "mma_mixed_martial_arts",
    "Boxing": "boxing_boxing",
}

# PrizePicks league IDs
PRIZEPICKS_LEAGUE_IDS = {
    "NFL": 9,
    "NBA": 7,
    "MLB": 2,
    "NHL": 12,
    "UFC/MMA": 8,
}

# Bookmakers to pull from
BOOKMAKERS = ["draftkings", "fanduel", "betmgm", "pointsbet", "caesars"]

CACHE_TTL_ODDS = 300       # 5 minutes for live odds
CACHE_TTL_STATS = 86400    # 24 hours for historical stats
CACHE_TTL_PRIZEPICKS = 300 # 5 minutes for PrizePicks
