"""
The Sharp — Sports Betting Analyzer
$30/month SaaS. Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Sharp",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.metric-card {
    background: #1e1e2e;
    border-radius: 10px;
    padding: 16px;
    margin: 6px 0;
    border-left: 4px solid #7c3aed;
}
.score-high { color: #22c55e; font-size: 2rem; font-weight: bold; }
.score-mid  { color: #eab308; font-size: 2rem; font-weight: bold; }
.score-low  { color: #ef4444; font-size: 2rem; font-weight: bold; }
.sharp-msg  { background: #1a1a2e; border-left: 3px solid #7c3aed;
              padding: 12px 16px; border-radius: 8px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

# ── Auth check ────────────────────────────────────────────────────────────────
from auth.auth_ui import init_session, is_logged_in, is_subscribed, render_login_page, render_paywall, render_user_menu

init_session()

# Not logged in → show login/signup page
if not is_logged_in():
    render_login_page()
    st.stop()

# Logged in but no subscription → show paywall
if not is_subscribed():
    render_paywall()
    st.stop()

# ── Lazy module loader ────────────────────────────────────────────────────────
@st.cache_resource
def load_modules():
    m = {}
    try:
        from data.odds_fetcher import get_odds, parse_games
        m["odds"] = (get_odds, parse_games)
    except Exception as e:
        m["odds_err"] = str(e)
    try:
        from data.prizepicks_fetcher import get_projections
        m["prizepicks"] = get_projections
    except Exception as e:
        m["prizepicks_err"] = str(e)
    try:
        from data.espn_fetcher import get_scoreboard
        m["espn"] = get_scoreboard
    except Exception as e:
        m["espn_err"] = str(e)
    try:
        from analysis.prop_analyzer import analyze_nfl_prop, analyze_nba_prop
        m["props"] = (analyze_nfl_prop, analyze_nba_prop)
    except Exception as e:
        m["props_err"] = str(e)
    try:
        from analysis.matchup_analyzer import analyze_nfl_h2h, analyze_nba_h2h
        m["h2h"] = (analyze_nfl_h2h, analyze_nba_h2h)
    except Exception as e:
        m["h2h_err"] = str(e)
    try:
        from analysis.confidence_scorer import score_prop
        m["scorer"] = score_prop
    except Exception as e:
        m["scorer_err"] = str(e)
    try:
        from ai.sharp_agent import chat as sharp_chat, get_quick_take
        m["sharp"] = (sharp_chat, get_quick_take)
    except Exception as e:
        m["sharp_err"] = str(e)
    return m

mods = load_modules()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏆 The Sharp")
    st.caption("Beat the books.")

    page = st.radio(
        "Navigation",
        ["💬 Ask The Sharp", "📊 Dashboard", "🔍 Line Analyzer",
         "📡 Live Odds", "⚔️ Matchup History", "🎯 Player Props"],
        index=0,
    )

    st.divider()
    sport = st.selectbox("Sport", ["NFL", "NBA", "MLB", "NHL", "UFC/MMA"])

    st.divider()
    render_user_menu()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ASK THE SHARP  (primary value-add)
# ═══════════════════════════════════════════════════════════════════════════════
if page == "💬 Ask The Sharp":
    st.title("💬 Ask The Sharp")
    st.caption("Your AI sharp bettor. Bring a line — I'll tell you what I think.")

    if "sharp_err" in mods:
        st.error(f"Sharp agent unavailable: {mods['sharp_err']}")
        st.info("Check your ANTHROPIC_API_KEY in .env")
        st.stop()

    sharp_chat, get_quick_take = mods["sharp"]

    # Initialize conversation
    if "sharp_messages" not in st.session_state:
        st.session_state.sharp_messages = []
    if "sharp_api_messages" not in st.session_state:
        st.session_state.sharp_api_messages = []

    # Starter prompts
    if not st.session_state.sharp_messages:
        st.markdown("""
        <div class='sharp-msg'>
            <strong>The Sharp:</strong> Alright, whatcha got? Drop a line on me — player prop,
            spread, total, whatever. I'll pull the numbers and tell you if it's worth a look
            or if you're walking into a trap.
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.caption("Try one of these:")
        cols = st.columns(3)
        starters = [
            "Dak Prescott over 275.5 passing yards vs NYG",
            "LeBron James over 25.5 points vs MIA",
            "Cowboys -3 vs Giants, what do you think?",
            "Chiefs over 27.5 points at home",
            "Steph Curry over 4.5 threes vs LAL",
            "Patriots under 21.5 points",
        ]
        for i, prompt in enumerate(starters):
            with cols[i % 3]:
                if st.button(prompt, key=f"starter_{i}", use_container_width=True):
                    st.session_state._quick_prompt = prompt
                    st.rerun()

    # Handle quick prompt from starter buttons
    if hasattr(st.session_state, "_quick_prompt") and st.session_state._quick_prompt:
        prompt = st.session_state._quick_prompt
        st.session_state._quick_prompt = None
        st.session_state.sharp_messages.append({"role": "user", "content": prompt})
        st.session_state.sharp_api_messages.append({"role": "user", "content": prompt})

        with st.spinner("The Sharp is looking at the numbers..."):
            response, updated = sharp_chat(st.session_state.sharp_api_messages, sport)

        st.session_state.sharp_messages.append({"role": "assistant", "content": response})
        st.session_state.sharp_api_messages = updated
        st.rerun()

    # Render conversation history
    for msg in st.session_state.sharp_messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🎯"):
                st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Drop a line... e.g. 'Dak over 330 yards vs MIA, thoughts?'")

    if user_input:
        st.session_state.sharp_messages.append({"role": "user", "content": user_input})
        st.session_state.sharp_api_messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant", avatar="🎯"):
            with st.spinner("Pulling the numbers..."):
                response, updated = sharp_chat(st.session_state.sharp_api_messages, sport)
            st.markdown(response)

        st.session_state.sharp_messages.append({"role": "assistant", "content": response})
        st.session_state.sharp_api_messages = updated

    # Conversation controls
    if st.session_state.sharp_messages:
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Clear Chat"):
                st.session_state.sharp_messages = []
                st.session_state.sharp_api_messages = []
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    st.title("📊 Dashboard")
    st.caption(f"Today: {datetime.now().strftime('%A, %B %d, %Y')}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Today's {sport} Games")
        if "espn" in mods:
            with st.spinner("Loading schedule..."):
                games = mods["espn"](sport)
            if games:
                df = pd.DataFrame(games)
                show = [c for c in ["away_team", "home_team", "status", "away_score", "home_score", "date"] if c in df.columns]
                st.dataframe(df[show], use_container_width=True, hide_index=True)
            else:
                st.info("No games today or data unavailable.")
        else:
            st.warning(f"ESPN unavailable: {mods.get('espn_err')}")

    with col2:
        st.subheader("Quick Stats")
        st.metric("Sport", sport)
        if "prizepicks" in mods:
            with st.spinner("Loading PrizePicks..."):
                pp = mods["prizepicks"](sport)
            st.metric("PrizePicks Lines", len(pp))

    st.divider()
    st.subheader(f"PrizePicks — {sport}")
    if "prizepicks" in mods:
        with st.spinner("Fetching lines..."):
            projs = mods["prizepicks"](sport)
        if projs:
            df_pp = pd.DataFrame(projs)
            show = [c for c in ["player", "team", "position", "stat_type", "line_score", "description"] if c in df_pp.columns]
            st.dataframe(df_pp[show].head(25), use_container_width=True, hide_index=True)
        else:
            st.info("No PrizePicks lines right now.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LINE ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Line Analyzer":
    st.title("🔍 Line Analyzer")
    st.caption("Drop in any prop for a hit rate, trend chart, and confidence score.")

    col_a, col_b = st.columns(2)
    with col_a:
        la_sport = st.selectbox("Sport", ["NFL", "NBA"], key="la_sport")
        player_name = st.text_input("Player Name", placeholder="e.g. Dak Prescott")
        stat_type = st.selectbox("Stat", {
            "NFL": ["passing_yards", "rushing_yards", "touchdowns", "completions", "interceptions"],
            "NBA": ["PTS", "REB", "AST", "FG3M", "BLK", "STL"],
        }.get(la_sport, ["PTS"]))
        line_value = st.number_input("Line", min_value=0.0, value=0.0, step=0.5)
    with col_b:
        opponent = st.text_input("Opponent (optional)", placeholder="e.g. MIA")
        analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

    if analyze_btn and player_name and line_value > 0:
        if "props" not in mods:
            st.error(f"Props unavailable: {mods.get('props_err')}")
        else:
            nfl_prop, nba_prop = mods["props"]
            score_prop = mods.get("scorer")
            with st.spinner("Pulling historical data..."):
                result = nfl_prop(player_name, stat_type, line_value, opponent or None) \
                    if la_sport == "NFL" else nba_prop(player_name, stat_type, line_value, opponent or None)

            if "error" in result:
                st.error(result["error"])
            else:
                scored = score_prop(result) if score_prop else {"score": 50, "label": "N/A", "summary": ""}
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Games", result.get("games_analyzed", 0))
                c2.metric("Avg", result.get("avg", 0))
                c3.metric("Last 5 Avg", result.get("last_5_avg", 0))
                c4.metric("Over %", f"{result.get('over_pct', 0)}%")

                score = scored["score"]
                cls = "score-high" if score >= 60 else "score-low" if score <= 40 else "score-mid"
                st.markdown(
                    f"<div class='metric-card'><span class='{cls}'>{score}</span>/100 — "
                    f"<strong>{scored['label']}</strong><br><small>{scored['summary']}</small></div>",
                    unsafe_allow_html=True,
                )

                last_10 = result.get("last_10_values", [])
                if last_10:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=[f"G-{len(last_10)-i}" for i in range(len(last_10))],
                        y=last_10,
                        marker_color=["#22c55e" if v > line_value else "#ef4444" for v in last_10],
                    ))
                    fig.add_hline(y=line_value, line_dash="dash", line_color="white",
                                  annotation_text=f"Line: {line_value}")
                    fig.update_layout(title=f"{player_name} — Last {len(last_10)} Games",
                                      template="plotly_dark", height=350)
                    st.plotly_chart(fig, use_container_width=True)

                if "sharp" in mods:
                    with st.expander("Get The Sharp's Take", expanded=True):
                        sharp_chat, _ = mods["sharp"]
                        line_desc = f"{player_name} {stat_type} over {line_value}" + (f" vs {opponent}" if opponent else "")
                        msgs = [{"role": "user", "content": f"Analyze this prop: {line_desc}. Here's the data: {result}"}]
                        with st.spinner("The Sharp is thinking..."):
                            take, _ = sharp_chat(msgs, la_sport)
                        st.markdown(take)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LIVE ODDS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📡 Live Odds":
    st.title("📡 Live Odds")
    tab1, tab2 = st.tabs(["Sportsbooks (DraftKings etc)", "PrizePicks"])

    with tab1:
        market = st.selectbox("Market", ["h2h (Moneyline)", "spreads", "totals"])
        mkt_key = market.split()[0]
        if "odds" not in mods:
            st.error(f"Add ODDS_API_KEY to .env for live sportsbook odds.\n{mods.get('odds_err', '')}")
        else:
            get_odds, parse_games = mods["odds"]
            with st.spinner("Fetching odds..."):
                raw = get_odds(sport, mkt_key)
                games = parse_games(raw)
            if not games:
                st.warning("No odds returned. Sport may be off-season, or check ODDS_API_KEY.")
            else:
                st.success(f"{len(games)} games found")
                for game in games:
                    with st.expander(f"{game['away_team']} @ {game['home_team']}  |  {str(game.get('commence_time',''))[:10]}"):
                        for book, markets in game.get("bookmakers", {}).items():
                            st.markdown(f"**{book.upper()}**")
                            for mk, outcomes in markets.items():
                                if mk == mkt_key:
                                    cols = st.columns(len(outcomes))
                                    for i, o in enumerate(outcomes):
                                        with cols[i]:
                                            price = o.get("price", "N/A")
                                            pt = o.get("point", "")
                                            pt_str = f" ({pt})" if pt != "" else ""
                                            prefix = "+" if isinstance(price, (int, float)) and price > 0 else ""
                                            st.metric(o.get("name", ""), f"{prefix}{price}{pt_str}")

    with tab2:
        if "prizepicks" not in mods:
            st.error(f"PrizePicks unavailable: {mods.get('prizepicks_err')}")
        else:
            with st.spinner("Loading PrizePicks..."):
                pp = mods["prizepicks"](sport)
            if not pp:
                st.warning("No lines available — sport may be out of season.")
            else:
                df = pd.DataFrame(pp)
                c1, c2 = st.columns(2)
                with c1:
                    stat_f = st.multiselect("Stat", sorted(df["stat_type"].unique()) if "stat_type" in df.columns else [])
                with c2:
                    team_f = st.multiselect("Team", sorted(df["team"].unique()) if "team" in df.columns else [])
                filtered = df.copy()
                if stat_f:
                    filtered = filtered[filtered["stat_type"].isin(stat_f)]
                if team_f:
                    filtered = filtered[filtered["team"].isin(team_f)]
                show = [c for c in ["player", "team", "position", "stat_type", "line_score", "description"] if c in filtered.columns]
                st.dataframe(filtered[show], use_container_width=True, hide_index=True)
                st.caption(f"Showing {len(filtered)} of {len(df)}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MATCHUP HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚔️ Matchup History":
    st.title("⚔️ Matchup History")
    c1, c2, c3 = st.columns(3)
    with c1:
        h2h_sport = st.selectbox("Sport", ["NFL", "NBA"], key="h2h_sport")
    with c2:
        t1 = st.text_input("Team 1", placeholder="e.g. DAL")
    with c3:
        t2 = st.text_input("Team 2", placeholder="e.g. GB")

    if h2h_sport == "NFL":
        seasons_back = st.slider("Seasons back", 2, 10, 5)

    if st.button("Get H2H History", type="primary") and t1 and t2:
        if "h2h" not in mods:
            st.error(f"H2H unavailable: {mods.get('h2h_err')}")
        else:
            nfl_h2h, nba_h2h = mods["h2h"]
            with st.spinner("Loading matchup history..."):
                if h2h_sport == "NFL":
                    yr = datetime.now().year
                    result = nfl_h2h(t1.upper(), t2.upper(), list(range(yr - seasons_back, yr)))
                else:
                    result = nba_h2h(t1, t2)

            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader(f"{result['team1']} vs {result['team2']}")
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Games", result["total_games"])
                mc2.metric(f"{result['team1']} W", result["team1_wins"])
                mc3.metric(f"{result['team2']} W", result["team2_wins"])
                mc4.metric(f"{result['team1']} Win%", f"{result['team1_win_pct']}%")
                if "avg_total_points" in result:
                    st.metric("Avg Total", result["avg_total_points"])

                games = result.get("games", [])
                if games:
                    st.dataframe(pd.DataFrame(games), use_container_width=True, hide_index=True)
                    fig = px.pie(
                        values=[result["team1_wins"], result["team2_wins"]],
                        names=[result["team1"], result["team2"]],
                        title="Win Distribution",
                        color_discrete_sequence=["#7c3aed", "#2563eb"],
                        template="plotly_dark",
                    )
                    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PLAYER PROPS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Player Props":
    st.title("🎯 Player Props")
    c1, c2 = st.columns(2)
    with c1:
        pp_sport = st.selectbox("Sport", ["NFL", "NBA"], key="pp_sport")
        pp_player = st.text_input("Player", placeholder="e.g. LeBron James")
        pp_stat = st.selectbox("Stat", {
            "NFL": ["passing_yards", "rushing_yards", "touchdowns", "completions"],
            "NBA": ["PTS", "REB", "AST", "FG3M", "BLK", "STL"],
        }.get(pp_sport, ["PTS"]))
    with c2:
        pp_line = st.number_input("Line", min_value=0.0, value=0.0, step=0.5)
        pp_opp = st.text_input("vs. Opponent (optional)", placeholder="e.g. MIA")
        if st.button("Analyze", type="primary", use_container_width=True) and pp_player:
            if "props" not in mods:
                st.error(f"Props unavailable: {mods.get('props_err')}")
            else:
                nfl_p, nba_p = mods["props"]
                score_prop = mods.get("scorer")
                with st.spinner(f"Looking up {pp_player}..."):
                    res = nfl_p(pp_player, pp_stat, pp_line or 0, pp_opp or None) \
                        if pp_sport == "NFL" else nba_p(pp_player, pp_stat, pp_line or 0, pp_opp or None)

                if "error" in res:
                    st.error(res["error"])
                else:
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Avg", res.get("avg", "N/A"))
                    mc2.metric("Games", res.get("games_analyzed", 0))
                    mc3.metric("Trend", res.get("trend", "N/A"))

                    if pp_line > 0 and score_prop:
                        sc = score_prop(res)
                        mc4, mc5 = st.columns(2)
                        mc4.metric("Over Hit %", f"{res.get('over_pct', 0)}%")
                        mc5.metric("Confidence", f"{sc['score']}/100 — {sc['label']}")

                    last_10 = res.get("last_10_values", [])
                    if last_10:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=list(range(1, len(last_10)+1)), y=last_10,
                            mode="lines+markers",
                            marker=dict(
                                color=["#22c55e" if v > (pp_line or res.get("avg", 0)) else "#ef4444" for v in last_10],
                                size=10,
                            ),
                            line=dict(color="#7c3aed"),
                        ))
                        if pp_line > 0:
                            fig.add_hline(y=pp_line, line_dash="dash", line_color="#eab308",
                                          annotation_text=f"Line: {pp_line}")
                        fig.add_hline(y=res.get("avg", 0), line_dash="dot", line_color="#6b7280",
                                      annotation_text=f"Avg: {res.get('avg', 0)}")
                        fig.update_layout(
                            title=f"{pp_player} — {pp_stat}" + (f" vs {pp_opp}" if pp_opp else ""),
                            template="plotly_dark", height=400,
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    st.session_state["_pp_result"] = res
                    st.session_state["_pp_line_desc"] = f"{pp_player} {pp_stat} {pp_line}" + (f" vs {pp_opp}" if pp_opp else "")
                    st.session_state["_pp_sport"] = pp_sport

    # Sharp take below the form
    if st.session_state.get("_pp_result") and "sharp" in mods:
        with st.expander("Get The Sharp's Take on This Prop", expanded=False):
            sharp_chat, _ = mods["sharp"]
            res = st.session_state["_pp_result"]
            line_desc = st.session_state.get("_pp_line_desc", "")
            spt = st.session_state.get("_pp_sport", "NFL")
            msgs = [{"role": "user", "content": f"What do you think about: {line_desc}? Data: {res}"}]
            with st.spinner("The Sharp is looking at it..."):
                take, _ = sharp_chat(msgs, spt)
            st.markdown(take)
