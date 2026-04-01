"""
Stripe billing integration — $30/month subscription.
Get keys at https://dashboard.stripe.com
"""
import time
from config import STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET, APP_URL
from db.cache import get, set, cache_key

try:
    import stripe as _stripe
    if STRIPE_SECRET_KEY:
        _stripe.api_key = STRIPE_SECRET_KEY
        STRIPE_AVAILABLE = True
    else:
        STRIPE_AVAILABLE = False
except ImportError:
    _stripe = None
    STRIPE_AVAILABLE = False


def create_checkout_session(user_id: str, email: str) -> str | None:
    """
    Creates a Stripe Checkout session for $30/month.
    Returns the checkout URL to redirect the user to.
    """
    if not STRIPE_AVAILABLE:
        return None
    try:
        session = _stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=["card"],
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            mode="subscription",
            success_url=f"{APP_URL}?subscribed=true",
            cancel_url=f"{APP_URL}?canceled=true",
            metadata={"user_id": user_id},
            subscription_data={"metadata": {"user_id": user_id}},
        )
        return session.url
    except Exception as e:
        print(f"[Stripe] Checkout error: {e}")
        return None


def create_portal_session(user_id: str, email: str) -> str | None:
    """
    Creates a Stripe Customer Portal session so users can manage/cancel.
    Returns portal URL.
    """
    if not STRIPE_AVAILABLE:
        return None
    try:
        customer = _find_customer(email)
        if not customer:
            return None
        session = _stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=APP_URL,
        )
        return session.url
    except Exception as e:
        print(f"[Stripe] Portal error: {e}")
        return None


def get_subscription_status(user_id: str, email: str) -> dict:
    """
    Checks if a user has an active subscription.
    Cached for 5 minutes to avoid hammering Stripe API.
    Returns: {"active": bool, "plan": str, "cancel_at": str|None}
    """
    if not STRIPE_AVAILABLE:
        return {"active": False, "plan": None, "cancel_at": None}

    ck = cache_key("stripe_sub", user_id)
    cached = get(ck)
    if cached is not None:
        return cached

    try:
        customer = _find_customer(email)
        if not customer:
            result = {"active": False, "plan": None, "cancel_at": None}
            set(ck, result, 300)
            return result

        subs = _stripe.Subscription.list(customer=customer.id, status="active", limit=1)
        if subs.data:
            sub = subs.data[0]
            result = {
                "active": True,
                "plan": sub.get("items", {}).get("data", [{}])[0].get("price", {}).get("nickname", "Monthly"),
                "cancel_at": sub.get("cancel_at"),
                "current_period_end": sub.get("current_period_end"),
            }
        else:
            result = {"active": False, "plan": None, "cancel_at": None}

        set(ck, result, 300)
        return result
    except Exception as e:
        print(f"[Stripe] Status check error: {e}")
        return {"active": False, "plan": None, "cancel_at": None}


def _find_customer(email: str):
    """Find a Stripe customer by email."""
    if not STRIPE_AVAILABLE:
        return None
    try:
        customers = _stripe.Customer.list(email=email, limit=1)
        return customers.data[0] if customers.data else None
    except Exception:
        return None


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """
    Validates and processes a Stripe webhook event.
    Call this from webhook_server.py
    """
    if not STRIPE_AVAILABLE or not STRIPE_WEBHOOK_SECRET:
        return {"error": "Stripe not configured"}
    try:
        event = _stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return {"error": str(e)}

    event_type = event["type"]

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        sub = event["data"]["object"]
        user_id = sub.get("metadata", {}).get("user_id")
        if user_id:
            # Bust the cache so next check is fresh
            ck = cache_key("stripe_sub", user_id)
            set(ck, None, 0)

    elif event_type == "customer.subscription.deleted":
        sub = event["data"]["object"]
        user_id = sub.get("metadata", {}).get("user_id")
        if user_id:
            ck = cache_key("stripe_sub", user_id)
            set(ck, {"active": False, "plan": None, "cancel_at": None}, 300)

    return {"received": True, "type": event_type}
