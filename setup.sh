#!/bin/bash
echo "Setting up The Sharp..."

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "Created .env — fill in your keys:"
    echo ""
    echo "  REQUIRED for AI (free, no credit card):"
    echo "    GROQ_API_KEY  → console.groq.com → Sign up → API Keys"
    echo ""
    echo "  REQUIRED for auth + billing:"
    echo "    SUPABASE_URL / SUPABASE_ANON_KEY  → supabase.com (free)"
    echo "    STRIPE_SECRET_KEY / STRIPE_PRICE_ID → dashboard.stripe.com"
    echo ""
    echo "  OPTIONAL (live DraftKings odds):"
    echo "    ODDS_API_KEY  → the-odds-api.com (free, 500 req/month)"
fi

echo ""
echo "Done! Start the app:"
echo "  source venv/bin/activate && streamlit run app.py"
echo ""
echo "To also run the Stripe webhook server (separate terminal):"
echo "  source venv/bin/activate && python -m billing.webhook_server"
