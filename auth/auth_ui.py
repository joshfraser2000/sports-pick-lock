"""
Streamlit login/signup UI components.
"""
import streamlit as st
from auth.supabase_client import sign_in, sign_up, sign_out, get_user, send_password_reset, SUPABASE_AVAILABLE
from billing.stripe_client import get_subscription_status, create_checkout_session, create_portal_session

PRICE_MONTHLY = 30


def init_session():
    for key in ("auth_token", "user", "subscription"):
        if key not in st.session_state:
            st.session_state[key] = None


def is_logged_in() -> bool:
    init_session()
    if not st.session_state.auth_token:
        return False
    user = get_user(st.session_state.auth_token)
    if not user:
        st.session_state.auth_token = None
        st.session_state.user = None
        return False
    st.session_state.user = user
    return True


def is_subscribed() -> bool:
    if not is_logged_in():
        return False
    user_id = st.session_state.user.get("id")
    email = st.session_state.user.get("email")
    sub = get_subscription_status(user_id, email)
    st.session_state.subscription = sub
    return sub.get("active", False)


def render_login_page():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #0a0a0f; }
    [data-testid="stHeader"] { background: transparent; }
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        letter-spacing: -2px;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 60%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin-bottom: 0;
    }
    .hero-sub {
        color: #6b7280;
        font-size: 1.1rem;
        margin-top: 8px;
        letter-spacing: 0.5px;
    }
    .stat-pill {
        display: inline-block;
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(124,58,237,0.3);
        border-radius: 999px;
        padding: 6px 16px;
        color: #a78bfa;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
    }
    .feature-row {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        padding: 14px 0;
        border-bottom: 1px solid #1f1f2e;
    }
    .feature-icon {
        font-size: 1.4rem;
        min-width: 32px;
        margin-top: 2px;
    }
    .feature-title { color: #f9fafb; font-weight: 700; font-size: 0.95rem; }
    .feature-desc  { color: #6b7280; font-size: 0.85rem; margin-top: 2px; }
    .login-card {
        background: #111118;
        border: 1px solid #1f1f2e;
        border-radius: 16px;
        padding: 32px;
    }
    .divider-text {
        text-align: center;
        color: #374151;
        font-size: 0.8rem;
        margin: 16px 0;
        position: relative;
    }
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.markdown("<div style='padding: 60px 20px 0'>", unsafe_allow_html=True)
        st.markdown("<p class='hero-title'>Pick Lock.</p>", unsafe_allow_html=True)
        st.markdown("<p class='hero-sub'>Stop guessing. Start winning.</p>", unsafe_allow_html=True)

        st.write("")
        st.markdown("""
        <div>
            <span class='stat-pill'>NFL</span>
            <span class='stat-pill'>NBA</span>
            <span class='stat-pill'>MLB</span>
            <span class='stat-pill'>NHL</span>
            <span class='stat-pill'>UFC</span>
            <span class='stat-pill'>Boxing</span>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.markdown("""
        <div style='margin-top: 24px'>
            <div class='feature-row'>
                <div class='feature-icon'>🎯</div>
                <div>
                    <div class='feature-title'>Your personal sharp</div>
                    <div class='feature-desc'>Drop any line. Get an honest debate — not hype, not filler. Real analysis based on actual historical data.</div>
                </div>
            </div>
            <div class='feature-row'>
                <div class='feature-icon'>📡</div>
                <div>
                    <div class='feature-title'>Live lines, all books</div>
                    <div class='feature-desc'>DraftKings, PrizePicks, FanDuel — all in one place, updated in real time.</div>
                </div>
            </div>
            <div class='feature-row'>
                <div class='feature-icon'>📊</div>
                <div>
                    <div class='feature-title'>Years of data, instant answers</div>
                    <div class='feature-desc'>Last 10 matchups. Player props vs specific opponents. Trend charts. Confidence scores.</div>
                </div>
            </div>
            <div class='feature-row' style='border-bottom:none'>
                <div class='feature-icon'>🔒</div>
                <div>
                    <div class='feature-title'>$30/month. Cancel anytime.</div>
                    <div class='feature-desc'>No annual contracts. No hidden fees. Just an edge.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.write("")
        st.write("")
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        if not SUPABASE_AVAILABLE:
            st.markdown("<h3 style='color:#f9fafb; margin-bottom:4px'>Get in.</h3>", unsafe_allow_html=True)
            st.caption("Auth not configured yet — running in dev mode.")
            _render_demo_bypass()
            st.markdown("</div>", unsafe_allow_html=True)
            return

        tab_login, tab_signup = st.tabs(["Log In", "Create Account"])
        with tab_login:
            _render_login_form()
        with tab_signup:
            _render_signup_form()

        st.markdown("</div>", unsafe_allow_html=True)


def _render_login_form():
    with st.form("login_form"):
        st.markdown("<div style='margin-bottom:8px'>", unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="you@example.com", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
        submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

        if submitted:
            if not email or not password:
                st.error("Enter your email and password.")
                return
            with st.spinner(""):
                result = sign_in(email, password)
            if result.get("error"):
                st.error(result["error"])
            else:
                st.session_state.auth_token = result["session"]["access_token"]
                st.session_state.user = result["user"]
                st.rerun()

    if st.button("Forgot password?", use_container_width=True):
        st.session_state["show_reset"] = True

    if st.session_state.get("show_reset"):
        reset_email = st.text_input("Email address", placeholder="you@example.com", key="reset_email")
        if st.button("Send Reset Link", use_container_width=True):
            r = send_password_reset(reset_email)
            if r.get("error"):
                st.error(r["error"])
            else:
                st.success("Check your email.")
                st.session_state["show_reset"] = False


def _render_signup_form():
    with st.form("signup_form"):
        email = st.text_input("Email", placeholder="you@example.com", key="su_email", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Password (8+ chars)", key="su_pass", label_visibility="collapsed")
        password2 = st.text_input("Confirm", type="password", placeholder="Confirm password", key="su_pass2", label_visibility="collapsed")
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
            with st.spinner(""):
                result = sign_up(email, password)
            if result.get("error"):
                st.error(result["error"])
            else:
                st.success("Account created! Check your email to confirm, then log in.")


def render_paywall():
    user_email = st.session_state.user.get("email", "") if st.session_state.user else ""
    user_id = st.session_state.user.get("id", "") if st.session_state.user else ""

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #0a0a0f; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.6, 1])
    with col_c:
        st.write("")
        st.write("")
        st.markdown("""
        <div style='text-align:center; margin-bottom:32px'>
            <p style='color:#6b7280; font-size:0.9rem; letter-spacing:2px; text-transform:uppercase; margin-bottom:8px'>One plan. No BS.</p>
            <h1 style='font-size:3.5rem; font-weight:900; color:#fff; margin:0'>$30<span style='font-size:1.2rem; color:#6b7280'>/mo</span></h1>
            <p style='color:#6b7280; margin-top:4px'>Cancel anytime.</p>
        </div>
        """, unsafe_allow_html=True)

        items = [
            ("🎯", "Your own sharp to debate every pick"),
            ("📡", "Live odds from every major book"),
            ("📊", "Deep historical stats for all 6 sports"),
            ("🔥", "Confidence scores on every line"),
            ("♾️", "Unlimited analysis, no caps"),
        ]
        for icon, text in items:
            st.markdown(f"""
            <div style='display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid #1f1f2e'>
                <span style='font-size:1.2rem'>{icon}</span>
                <span style='color:#d1d5db; font-size:0.95rem'>{text}</span>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        from billing.stripe_client import STRIPE_AVAILABLE
        if STRIPE_AVAILABLE:
            checkout_url = create_checkout_session(user_id, user_email)
            if checkout_url:
                st.link_button("Unlock Pick Lock — $30/month", checkout_url, use_container_width=True, type="primary")
            else:
                st.error("Could not create checkout. Check STRIPE_SECRET_KEY.")
        else:
            st.warning("Stripe not configured yet.")
            _render_demo_bypass()

        st.write("")
        st.caption(f"Signed in as {user_email}")
        if st.button("Log Out", use_container_width=True):
            _do_logout()


def render_user_menu():
    user_email = st.session_state.user.get("email", "") if st.session_state.user else ""
    user_id = st.session_state.user.get("id", "") if st.session_state.user else ""

    st.caption(f"{user_email}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Billing", use_container_width=True, key="billing_btn"):
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
    if st.button("Enter App", type="primary", use_container_width=True):
        st.session_state.auth_token = "dev_token"
        st.session_state.user = {"id": "dev", "email": "dev@local"}
        st.session_state.subscription = {"active": True, "plan": "dev"}
        st.rerun()
