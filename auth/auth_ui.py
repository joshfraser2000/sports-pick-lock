"""
Streamlit login/signup UI components.
"""
import streamlit as st
from auth.supabase_client import sign_in, sign_up, sign_out, get_user, send_password_reset, SUPABASE_AVAILABLE
from billing.stripe_client import get_subscription_status, create_checkout_session, create_portal_session

PRICE_MONTHLY = 30  # dollars


def init_session():
    """Initialize auth session state."""
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "subscription" not in st.session_state:
        st.session_state.subscription = None


def is_logged_in() -> bool:
    init_session()
    if not st.session_state.auth_token:
        return False
    # Re-validate token
    user = get_user(st.session_state.auth_token)
    if not user:
        st.session_state.auth_token = None
        st.session_state.user = None
        return False
    st.session_state.user = user
    return True


def is_subscribed() -> bool:
    """Returns True if user has an active subscription."""
    if not is_logged_in():
        return False

    # Re-check subscription (cached in billing module)
    user_id = st.session_state.user.get("id")
    email = st.session_state.user.get("email")
    sub = get_subscription_status(user_id, email)
    st.session_state.subscription = sub
    return sub.get("active", False)


def render_login_page():
    """Renders the full login/signup/paywall page."""
    st.markdown("""
    <div style='text-align:center; padding: 40px 0 20px'>
        <h1>🏆 The Sharp</h1>
        <p style='color:#9ca3af; font-size:1.1rem'>
            AI-powered sports betting analysis. Beat the books.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        # Feature highlights
        st.markdown("""
        <div style='background:#1e1e2e; border-radius:12px; padding:20px; margin-bottom:24px'>
            <h4 style='color:#7c3aed'>What you get for $30/month</h4>
            <ul style='color:#d1d5db; line-height:2'>
                <li>AI sharp bettor debates every pick with you</li>
                <li>Live odds from DraftKings, PrizePicks & more</li>
                <li>Historical matchup & player prop analysis</li>
                <li>NFL, NBA, MLB, NHL, UFC, Boxing</li>
                <li>Confidence scores on every line</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if not SUPABASE_AVAILABLE:
            st.warning("Auth not configured yet. Add SUPABASE_URL and SUPABASE_ANON_KEY to .env")
            _render_demo_bypass()
            return

        tab_login, tab_signup = st.tabs(["Log In", "Create Account"])

        with tab_login:
            _render_login_form()

        with tab_signup:
            _render_signup_form()


def _render_login_form():
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Enter your email and password.")
                return
            with st.spinner("Logging in..."):
                result = sign_in(email, password)
            if result.get("error"):
                st.error(result["error"])
            else:
                st.session_state.auth_token = result["session"]["access_token"]
                st.session_state.user = result["user"]
                st.success("Logged in!")
                st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Forgot password?", use_container_width=True):
            st.session_state["show_reset"] = True

    if st.session_state.get("show_reset"):
        reset_email = st.text_input("Enter your email to reset password")
        if st.button("Send Reset Link"):
            r = send_password_reset(reset_email)
            if r.get("error"):
                st.error(r["error"])
            else:
                st.success("Check your email for a reset link.")
                st.session_state["show_reset"] = False


def _render_signup_form():
    with st.form("signup_form"):
        email = st.text_input("Email", placeholder="you@example.com", key="su_email")
        password = st.text_input("Password", type="password", key="su_pass",
                                  help="At least 8 characters")
        password2 = st.text_input("Confirm Password", type="password", key="su_pass2")
        agree = st.checkbox("I agree to the Terms of Service")
        submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("All fields required.")
                return
            if password != password2:
                st.error("Passwords don't match.")
                return
            if len(password) < 8:
                st.error("Password must be at least 8 characters.")
                return
            if not agree:
                st.error("You must agree to the Terms of Service.")
                return
            with st.spinner("Creating account..."):
                result = sign_up(email, password)
            if result.get("error"):
                st.error(result["error"])
            else:
                st.success("Account created! Check your email to confirm, then log in.")


def render_paywall():
    """Shown to logged-in users who don't have an active subscription."""
    user_email = st.session_state.user.get("email", "") if st.session_state.user else ""
    user_id = st.session_state.user.get("id", "") if st.session_state.user else ""

    st.markdown("""
    <div style='text-align:center; padding:40px 0'>
        <h2>Subscribe to unlock The Sharp</h2>
        <p style='color:#9ca3af'>$30/month — cancel anytime</p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
        <div style='background:#1e1e2e; border-radius:12px; padding:24px; text-align:center'>
            <h3 style='color:#7c3aed'>The Sharp — Monthly</h3>
            <h1 style='font-size:3rem'>$30<span style='font-size:1rem;color:#9ca3af'>/month</span></h1>
            <hr style='border-color:#374151'>
            <ul style='text-align:left; color:#d1d5db; line-height:2.2'>
                <li>AI sharp bettor debates picks 24/7</li>
                <li>Live odds: DraftKings, PrizePicks, FanDuel</li>
                <li>Full historical database (NFL, NBA, MLB, NHL, UFC)</li>
                <li>Confidence scores + trend charts</li>
                <li>Unlimited line analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        from billing.stripe_client import STRIPE_AVAILABLE
        if STRIPE_AVAILABLE:
            checkout_url = create_checkout_session(user_id, user_email)
            if checkout_url:
                st.link_button("Subscribe Now — $30/month", checkout_url, use_container_width=True, type="primary")
            else:
                st.error("Could not create checkout session. Check STRIPE_SECRET_KEY in .env")
        else:
            st.warning("Stripe not configured. Add STRIPE_SECRET_KEY and STRIPE_PRICE_ID to .env")
            _render_demo_bypass()

        st.divider()
        st.caption(f"Logged in as {user_email}")
        if st.button("Log Out", use_container_width=True):
            _do_logout()


def render_user_menu():
    """Compact user menu shown in the sidebar when logged in."""
    user_email = st.session_state.user.get("email", "") if st.session_state.user else ""
    user_id = st.session_state.user.get("id", "") if st.session_state.user else ""

    st.caption(f"Logged in: {user_email}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Manage Billing", use_container_width=True, key="billing_btn"):
            portal_url = create_portal_session(user_id, user_email)
            if portal_url:
                st.markdown(f'<meta http-equiv="refresh" content="0; url={portal_url}">', unsafe_allow_html=True)
            else:
                st.warning("Billing portal unavailable.")
    with col2:
        if st.button("Log Out", use_container_width=True, key="logout_btn"):
            _do_logout()


def _do_logout():
    if st.session_state.auth_token:
        sign_out(st.session_state.auth_token)
    st.session_state.auth_token = None
    st.session_state.user = None
    st.session_state.subscription = None
    st.rerun()


def _render_demo_bypass():
    """Dev-only bypass when auth/billing isn't configured yet."""
    st.divider()
    st.caption("Dev mode: auth/billing not fully configured")
    if st.button("Enter App (Dev Mode)", type="secondary", use_container_width=True):
        st.session_state.auth_token = "dev_token"
        st.session_state.user = {"id": "dev", "email": "dev@local"}
        st.session_state.subscription = {"active": True, "plan": "dev"}
        st.rerun()
