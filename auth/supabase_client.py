"""
Supabase auth integration.
Free tier: https://supabase.com (50k MAU, no credit card needed)
"""
import os
from config import SUPABASE_URL, SUPABASE_ANON_KEY

try:
    from supabase import create_client, Client
    _sb: Client | None = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL and SUPABASE_ANON_KEY else None
    SUPABASE_AVAILABLE = _sb is not None
except ImportError:
    _sb = None
    SUPABASE_AVAILABLE = False


def sign_up(email: str, password: str) -> dict:
    """Create a new account. Returns {"user": ..., "error": ...}"""
    if not _sb:
        return {"error": "Supabase not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY to .env"}
    try:
        res = _sb.auth.sign_up({"email": email, "password": password})
        if res.user:
            return {"user": {"id": res.user.id, "email": res.user.email}, "error": None}
        return {"error": "Sign up failed — check your email for a confirmation link."}
    except Exception as e:
        msg = str(e)
        if "already registered" in msg.lower():
            return {"error": "This email is already registered. Try logging in."}
        return {"error": msg}


def sign_in(email: str, password: str) -> dict:
    """Sign in. Returns {"user": ..., "session": ..., "error": ...}"""
    if not _sb:
        return {"error": "Supabase not configured."}
    try:
        res = _sb.auth.sign_in_with_password({"email": email, "password": password})
        if res.user and res.session:
            return {
                "user": {"id": res.user.id, "email": res.user.email},
                "session": {"access_token": res.session.access_token},
                "error": None,
            }
        return {"error": "Login failed. Check your email and password."}
    except Exception as e:
        msg = str(e)
        if "invalid" in msg.lower() or "credentials" in msg.lower():
            return {"error": "Wrong email or password."}
        return {"error": msg}


def sign_out(access_token: str) -> None:
    if not _sb:
        return
    try:
        _sb.auth.sign_out()
    except Exception:
        pass


def get_user(access_token: str) -> dict | None:
    """Validate an access token and return user info."""
    if not _sb or not access_token:
        return None
    try:
        res = _sb.auth.get_user(access_token)
        if res.user:
            return {"id": res.user.id, "email": res.user.email}
    except Exception:
        pass
    return None


def send_password_reset(email: str) -> dict:
    if not _sb:
        return {"error": "Supabase not configured."}
    try:
        _sb.auth.reset_password_email(email)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}
