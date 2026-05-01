import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.tournament_config import (
    ROUND_OF_16_PAIRINGS, QUARTER_FINAL_PAIRINGS, SEMI_FINAL_PAIRINGS,
    FINAL_MATCH, BRACKET_ROUNDS, CONFEDERATION, CONFEDERATION_COLORS,
    FIFA_2026_RANK, groups,
)
from services.bracket_service import cascade_bracket, get_matchup_probs, build_r32_bracket

# CONSTANTS
ROUND_DISPLAY_ORDER = ["Round of 32", "Round of 16", "Quarter-Final", "Semi-Final", "Final"]

ROUND_ACCENT = {
    "Round of 32": "#64748b", "Round of 16": "#3b82f6",
    "Quarter-Final": "#10b981", "Semi-Final": "#ef4444", "Final": "#f59e0b",
}

FLAG_EMOJI = {
    "Argentina": "🇦🇷", "France": "🇫🇷", "Spain": "🇪🇸", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Brazil": "🇧🇷", "Portugal": "🇵🇹", "Belgium": "🇧🇪", "Netherlands": "🇳🇱",
    "Germany": "🇩🇪", "Croatia": "🇭🇷", "Morocco": "🇲🇦", "United States": "🇺🇸",
    "Colombia": "🇨🇴", "Mexico": "🇲🇽", "Japan": "🇯🇵", "Uruguay": "🇺🇾",
    "Senegal": "🇸🇳", "Switzerland": "🇨🇭", "Iran": "🇮🇷", "South Korea": "🇰🇷",
    "Australia": "🇦🇺", "Austria": "🇦🇹", "Ecuador": "🇪🇨", "Turkey": "🇹🇷",
    "Sweden": "🇸🇪", "Norway": "🇳🇴", "Algeria": "🇩🇿", "Egypt": "🇪🇬",
    "Czech Republic": "🇨🇿", "Qatar": "🇶🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Canada": "🇨🇦",
    "Ivory Coast": "🇨🇮", "Tunisia": "🇹🇳", "Paraguay": "🇵🇾", "Saudi Arabia": "🇸🇦",
    "DR Congo": "🇨🇩", "Ghana": "🇬🇭", "Bosnia and Herzegovina": "🇧🇦",
    "South Africa": "🇿🇦", "Jordan": "🇯🇴", "Cape Verde": "🇨🇻", "Iraq": "🇮🇶",
    "Uzbekistan": "🇺🇿", "Panama": "🇵🇦", "New Zealand": "🇳🇿", "Haiti": "🇭🇹",
    "Curaçao": "🇨🇼",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');
.match-card {
    background: #0f172a; border: 1px solid #1e293b; border-radius: 10px;
    padding: 0.75rem 1rem; margin-bottom: 0.6rem; position: relative; overflow: hidden;
}
.match-card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px; border-radius: 3px 0 0 3px;
}
.match-card.r32::before  { background: #64748b; }
.match-card.r16::before  { background: #3b82f6; }
.match-card.qf::before   { background: #10b981; }
.match-card.sf::before   { background: #ef4444; }
.match-card.final::before { background: #f59e0b; }
.match-id { font-size: 0.65rem; color: #475569; font-weight: 600; margin-bottom: 0.4rem; }
.prob-bar-bg {
    height: 6px; background: #1e293b; border-radius: 3px;
    overflow: hidden; display: flex; margin-top: 0.3rem;
}
.prob-bar-home { background: #3b82f6; height: 100%; }
.prob-bar-draw { background: #475569; height: 100%; }
.prob-bar-away { background: #ef4444; height: 100%; }
.progress-row { display: flex; gap: 0.4rem; margin-bottom: 1rem; flex-wrap: wrap; }
.progress-pill { font-size: 0.7rem; padding: 0.2rem 0.6rem; border-radius: 20px; font-weight: 500; }
.progress-pill.done   { background: #14532d; color: #86efac; }
.progress-pill.active { background: #1e3a5f; color: #93c5fd; }
.progress-pill.todo   { background: #1e293b; color: #475569; }
.round-header { display: flex; align-items: center; gap: 0.75rem; margin: 1.5rem 0 0.75rem; }
.round-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.round-label { font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem; letter-spacing: 0.1em; color: #94a3b8; }
.round-count { font-size: 0.7rem; color: #475569; margin-left: auto; }
.info-panel { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 1.25rem; }
.stat-row { display: flex; justify-content: space-between; align-items: center;
            padding: 0.35rem 0; border-bottom: 1px solid #1e293b; font-size: 0.85rem; }
.stat-row:last-child { border-bottom: none; }
.stat-label { color: #64748b; }
.stat-value { color: #e2e8f0; font-weight: 500; }
.stat-value.gold { color: #f59e0b; }
</style>
"""

def flag(team: Optional[str]) -> str:
    return FLAG_EMOJI.get(team or "", "🏳️")

def round_css_class(round_name: str) -> str:
    return {"Round of 32": "r32", "Round of 16": "r16", "Quarter-Final": "qf",
            "Semi-Final": "sf", "Final": "final"}.get(round_name, "r32")

def _round_header(round_name: str, n: int) -> str:
    color = ROUND_ACCENT.get(round_name, "#64748b")
    return f"""<div class="round-header">
      <div class="round-dot" style="background:{color}"></div>
      <span class="round-label">{round_name}</span>
      <span class="round-count">{n} match{'es' if n != 1 else ''}</span>
    </div>"""

# GROUP QUALIFIED TEAMS 

@st.cache_data
def get_group_qualified(group_df: pd.DataFrame) -> Tuple[Dict, Dict, List]:
    winners: Dict[str, str] = {}
    runners_up: Dict[str, str] = {}
    thirds_raw: List[Dict] = []

    for gname, teams in groups.items():
        letter = gname.replace("Group ", "")
        if group_df.empty or "Group" not in group_df.columns:
            ranked = sorted(teams, key=lambda t: FIFA_2026_RANK.get(t, 99))
            winners[letter] = ranked[0]
            runners_up[letter] = ranked[1]
            thirds_raw.append({"team": ranked[2], "points": 0, "group": letter})
        else:
            gdf = group_df[group_df["Group"] == gname].copy()
            if gdf.empty:
                ranked = sorted(teams, key=lambda t: FIFA_2026_RANK.get(t, 99))
                winners[letter] = ranked[0]; runners_up[letter] = ranked[1]
                thirds_raw.append({"team": ranked[2], "points": 0, "group": letter})
            else:
                sc = "1st_Place_Prob" if "1st_Place_Prob" in gdf.columns else "Advance_Prob"
                team_list = gdf.sort_values(sc, ascending=False)["Team"].tolist() if "Team" in gdf.columns else teams
                if len(team_list) >= 2:
                    winners[letter] = team_list[0]; runners_up[letter] = team_list[1]
                if len(team_list) >= 3:
                    thirds_raw.append({"team": team_list[2],
                                       "points": float(gdf.sort_values(sc, ascending=False).iloc[2].get("Advance_Prob", 0)),
                                       "group": letter})

    best_8 = [t["team"] for t in sorted(thirds_raw, key=lambda x: x["points"], reverse=True)[:8]]
    return winners, runners_up, best_8

# MANUAL BRACKET

def render_manual_bracket(matchup_df: pd.DataFrame, group_df: pd.DataFrame):
    st.markdown("""
    <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;
                padding:1rem 1.25rem;margin-bottom:1rem;'>
      <div style='color:#94a3b8;font-size:0.85rem;'>
        <strong>Make your predictions!</strong> Pick the winner of each match.
        Your picks cascade automatically into later rounds.
      </div>
    </div>""", unsafe_allow_html=True)

    # Init session state
    if "manual_picks" not in st.session_state:
        st.session_state.manual_picks = {}
    if "manual_r32" not in st.session_state:
        winners, runners_up, best_8 = get_group_qualified(group_df)
        st.session_state.manual_r32 = build_r32_bracket(winners, runners_up, best_8)

    picks = st.session_state.manual_picks
    r32   = st.session_state.manual_r32

    # Progress pills
    stages = [("R32", sum(1 for m in range(73, 89) if picks.get(m)), 16),
              ("R16", sum(1 for m in range(89, 97) if picks.get(m)), 8),
              ("QF",  sum(1 for m in range(97, 101) if picks.get(m)), 4),
              ("SF",  sum(1 for m in range(101, 103) if picks.get(m)), 2),
              ("Final", 1 if picks.get(103) else 0, 1)]
    pills = '<div class="progress-row">'
    for label, done, total in stages:
        cls = "done" if done == total else ("active" if done > 0 else "todo")
        pills += f'<span class="progress-pill {cls}">{label} {done}/{total}</span>'
    pills += "</div>"
    st.markdown(pills, unsafe_allow_html=True)

    # Buttons
    _, c2, c3 = st.columns([4, 2, 1])
    with c2:
        if st.button("💾 Save Bracket", use_container_width=True):
            st.session_state.saved_picks = picks.copy()
            st.success("Saved!")
    with c3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.manual_picks = {}
            st.rerun()

    # Cascade
    cascade_state = cascade_bracket(picks, matchup_df)

    def get_teams(mid):
        if mid in r32: return r32[mid]
        cs = cascade_state.get(mid, {})
        return cs.get("team1"), cs.get("team2")

    def render_pick(mid, round_name, container):
        t1, t2 = get_teams(mid)
        if not t1 and not t2:
            container.markdown(
                f'<div class="match-card {round_css_class(round_name)}">'
                f'<div class="match-id">M{mid}</div>'
                f'<div style="color:#475569;font-size:0.8rem;">Awaiting previous round</div>'
                f'</div>', unsafe_allow_html=True)
            return

        probs = get_matchup_probs(t1, t2, matchup_df) if t1 and t2 else None
        current_pick = picks.get(mid)

        prob_bar = ""
        if probs:
            hw, dr, aw = probs["home_win"], probs["draw"], probs["away_win"]
            prob_bar = f"""<div class="prob-bar-bg">
              <div class="prob-bar-home" style="width:{hw}%"></div>
              <div class="prob-bar-draw" style="width:{dr}%"></div>
              <div class="prob-bar-away" style="width:{aw}%"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#64748b;">
              <span>{hw:.0f}%</span><span>Draw {dr:.0f}%</span><span>{aw:.0f}%</span>
            </div>"""

        winner_html = ""
        if current_pick:
            loser = t2 if current_pick == t1 else t1
            winner_html = (f'<div style="margin-top:0.4rem;font-size:0.8rem;">'
                           f'<span style="color:#f59e0b;font-weight:600;">✓ {flag(current_pick)} {current_pick}</span>'
                           f' &nbsp; <span style="color:#475569;text-decoration:line-through;">{flag(loser)} {loser}</span>'
                           f'</div>')

        container.markdown(
            f'<div class="match-card {round_css_class(round_name)}">'
            f'<div class="match-id">M{mid} · {round_name}</div>'
            f'<div style="font-size:0.9rem;font-weight:500;color:#e2e8f0;margin:0.3rem 0;">'
            f'{flag(t1)} {t1 or "TBD"}  vs  {flag(t2)} {t2 or "TBD"}</div>'
            f'{prob_bar}{winner_html}</div>', unsafe_allow_html=True)

        if t1 and t2:
            options = ["— pick winner —", t1, t2]
            default_idx = 1 if current_pick == t1 else (2 if current_pick == t2 else 0)
            choice = container.selectbox(f"M{mid}", options, index=default_idx,
                                         label_visibility="collapsed", key=f"pick_{mid}")
            if choice != "— pick winner —" and choice != current_pick:
                st.session_state.manual_picks[mid] = choice
                st.rerun()

    # Render all rounds
    for round_name in ROUND_DISPLAY_ORDER:
        match_ids = sorted(BRACKET_ROUNDS.get(round_name, []))
        if not match_ids: continue
        color = ROUND_ACCENT.get(round_name, "#64748b")
        st.markdown(_round_header(round_name, len(match_ids)), unsafe_allow_html=True)
        n_cols = min(len(match_ids), 8)
        cols = st.columns(n_cols)
        for idx, mid in enumerate(match_ids):
            render_pick(mid, round_name, cols[idx % n_cols])
        st.divider()

    # Champion reveal
    champion = picks.get(FINAL_MATCH)
    if champion:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1c1400,#2d1f00);
                    border:2px solid #f59e0b;border-radius:16px;
                    padding:2rem;text-align:center;margin-top:1rem;">
            <div style="font-size:0.75rem;letter-spacing:0.3em;color:#b45309;">
                🏆 YOUR PREDICTED CHAMPION 🏆</div>
            <div style="font-size:3rem;font-weight:bold;color:#f59e0b;margin:0.5rem 0;">
                {flag(champion)} {champion}</div>
        </div>""", unsafe_allow_html=True)
        st.balloons()
    else:
        remaining = 16 - sum(1 for m in range(73, 89) if picks.get(m))
        if remaining > 0:
            st.info(f"👆 {remaining} Round of 32 match{'es' if remaining != 1 else ''} remaining — keep picking!")

    # Sidebar summary
    with st.sidebar:
        st.markdown("### 🖊️ Your Picks")
        if not picks:
            st.caption("No picks yet")
        else:
            for round_name in ROUND_DISPLAY_ORDER:
                round_picks = [(m, picks[m]) for m in sorted(BRACKET_ROUNDS.get(round_name, [])) if m in picks]
                if round_picks:
                    st.markdown(f"**{round_name}**")
                    for mid, winner in round_picks[:4]:
                        st.markdown(f"• M{mid}: {flag(winner)} {winner}")
                    if len(round_picks) > 4:
                        st.caption(f"+{len(round_picks) - 4} more")

# MATCHUP LOOKUP 

def render_matchup_lookup(matchup_df: pd.DataFrame):
    from config.tournament_config import ALL_TEAMS
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Match Predictor")
    all_teams = sorted(ALL_TEAMS)
    h = st.sidebar.selectbox("Home team", all_teams, key="lookup_home")
    a = st.sidebar.selectbox("Away team", all_teams, key="lookup_away", index=1)

    if h == a:
        st.sidebar.warning("Pick two different teams")
        return

    probs = get_matchup_probs(h, a, matchup_df)
    if probs is None:
        st.sidebar.error("No data for this matchup")
        return

    hw, dr, aw = probs["home_win"], probs["draw"], probs["away_win"]
    hg, ag     = probs["home_goals"], probs["away_goals"]
    st.sidebar.markdown(f"""
    <div class="info-panel">
      <div style="font-weight:600;color:#f1f5f9;margin-bottom:0.75rem;">
        {flag(h)} {h} vs {flag(a)} {a}</div>
      <div class="stat-row"><span class="stat-label">{h} win</span>
        <span class="stat-value gold">{hw:.1f}%</span></div>
      <div class="stat-row"><span class="stat-label">Draw</span>
        <span class="stat-value">{dr:.1f}%</span></div>
      <div class="stat-row"><span class="stat-label">{a} win</span>
        <span class="stat-value">{aw:.1f}%</span></div>
      <div class="stat-row"><span class="stat-label">xG {h}</span>
        <span class="stat-value">{hg:.2f}</span></div>
      <div class="stat-row"><span class="stat-label">xG {a}</span>
        <span class="stat-value">{ag:.2f}</span></div>
    </div>""", unsafe_allow_html=True)

# MAIN ENTRY POINT  
def render_bracket_page(
    matchup_df: pd.DataFrame = None,
    knockout_df: pd.DataFrame = None,
    group_df: pd.DataFrame = None,
):
    """
    Interactive bracket page.
    """
    st.markdown(CSS, unsafe_allow_html=True)

    if matchup_df is None:
        st.error("Matchup data not loaded. Please restart the app.")
        return

    # group_df fallback to empty if not passed
    if group_df is None:
        group_df = pd.DataFrame()

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b);
                border:1px solid #334155;border-radius:12px;
                padding:1.5rem 2rem;margin-bottom:1.5rem;">
      <p style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                letter-spacing:0.08em;margin:0;line-height:1;color:#f1f5f9;">
        🏆 WC 2026 Interactive Bracket</p>
      <p style="color:#94a3b8;font-size:0.85rem;margin-top:0.3rem;">
        Pick winners in each match — your bracket cascades automatically into later rounds.
      </p>
    </div>""", unsafe_allow_html=True)

    render_manual_bracket(matchup_df, group_df)
    render_matchup_lookup(matchup_df)