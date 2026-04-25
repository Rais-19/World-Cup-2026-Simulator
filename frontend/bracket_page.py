import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple

from services.bracket_service import bracket_service, cascade_bracket
from config.tournament_config import (
    ROUND_OF_16_PAIRINGS,
    QUARTER_FINAL_PAIRINGS,
    SEMI_FINAL_PAIRINGS,
    FINAL_MATCH,
    BRACKET_ROUNDS,
    CONFEDERATION,
    CONFEDERATION_COLORS,
    FIFA_2026_RANK,
    groups,
)

# ─────────────────────────────────────────────────────────────────
# CONSTANTS & STYLING
# ─────────────────────────────────────────────────────────────────

ROUND_DISPLAY_ORDER = [
    "Round of 32",
    "Round of 16",
    "Quarter-Final",
    "Semi-Final",
    "Final",
]

ROUND_COLORS = {
    "Round of 32":   "#334155",
    "Round of 16":   "#1e3a5f",
    "Quarter-Final": "#1a3a2a",
    "Semi-Final":    "#3b1f1f",
    "Final":         "#2d1b00",
}

ROUND_ACCENT = {
    "Round of 32":   "#64748b",
    "Round of 16":   "#3b82f6",
    "Quarter-Final": "#10b981",
    "Semi-Final":    "#ef4444",
    "Final":         "#f59e0b",
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

.bracket-page { font-family: 'DM Sans', sans-serif; }

/* ── Mode header ──────────────────────────────── */
.mode-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.mode-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    letter-spacing: 0.08em;
    margin: 0;
    line-height: 1;
}
.mode-subtitle {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-top: 0.3rem;
    font-weight: 300;
}

/* ── Match card ─────────────────────────────── */
.match-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s;
    position: relative;
    overflow: hidden;
}
.match-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    border-radius: 3px 0 0 3px;
}
.match-card.r32::before  { background: #64748b; }
.match-card.r16::before  { background: #3b82f6; }
.match-card.qf::before   { background: #10b981; }
.match-card.sf::before   { background: #ef4444; }
.match-card.final::before { background: #f59e0b; }
.match-card:hover { border-color: #334155; }

.match-id {
    font-size: 0.65rem;
    color: #475569;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.team-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.25rem 0;
}
.team-name {
    font-size: 0.9rem;
    font-weight: 500;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.team-name.winner {
    color: #f59e0b;
    font-weight: 600;
}
.team-name.loser {
    color: #475569;
}
.win-prob {
    font-size: 0.75rem;
    color: #64748b;
    font-variant-numeric: tabular-nums;
}
.win-prob.winner { color: #f59e0b; font-weight: 600; }
.vs-divider {
    border: none;
    border-top: 1px solid #1e293b;
    margin: 0.25rem 0;
}

/* ── Champion card ──────────────────────────── */
.champion-banner {
    background: linear-gradient(135deg, #1c1400 0%, #2d1f00 50%, #1c1400 100%);
    border: 1px solid #f59e0b44;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    margin: 1rem 0 2rem;
    position: relative;
    overflow: hidden;
}
.champion-banner::after {
    content: '🏆';
    position: absolute;
    font-size: 8rem;
    opacity: 0.06;
    right: -1rem;
    top: -1rem;
    pointer-events: none;
}
.champion-label {
    font-size: 0.7rem;
    letter-spacing: 0.3em;
    color: #b45309;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.champion-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    letter-spacing: 0.05em;
    color: #f59e0b;
    line-height: 1;
    margin: 0;
}
.champion-prob {
    color: #92400e;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}

/* ── Round header ───────────────────────────── */
.round-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1.5rem 0 0.75rem;
}
.round-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.round-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    letter-spacing: 0.1em;
    color: #94a3b8;
}
.round-count {
    font-size: 0.7rem;
    color: #475569;
    margin-left: auto;
}

/* ── Probability bar ────────────────────────── */
.prob-bar-wrap { margin-top: 0.5rem; }
.prob-bar-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.7rem;
    color: #64748b;
    margin-bottom: 0.2rem;
}
.prob-bar-bg {
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
    overflow: hidden;
    display: flex;
}
.prob-bar-home { background: #3b82f6; height: 100%; }
.prob-bar-draw { background: #475569; height: 100%; }
.prob-bar-away { background: #ef4444; height: 100%; }

/* ── Manual pick badge ──────────────────────── */
.pick-badge {
    display: inline-block;
    background: #1e3a5f;
    color: #93c5fd;
    font-size: 0.65rem;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    letter-spacing: 0.05em;
    font-weight: 600;
    vertical-align: middle;
    margin-left: 0.3rem;
}

/* ── Info panel ─────────────────────────────── */
.info-panel {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.25rem;
}
.info-panel h4 {
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 0.08em;
    font-size: 1.1rem;
    color: #f1f5f9;
    margin: 0 0 0.75rem;
}
.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.35rem 0;
    border-bottom: 1px solid #1e293b;
    font-size: 0.85rem;
}
.stat-row:last-child { border-bottom: none; }
.stat-label { color: #64748b; }
.stat-value { color: #e2e8f0; font-weight: 500; font-variant-numeric: tabular-nums; }
.stat-value.gold { color: #f59e0b; }

/* ── Progress tracker ───────────────────────── */
.progress-row {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}
.progress-pill {
    font-size: 0.7rem;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-weight: 500;
}
.progress-pill.done   { background: #14532d; color: #86efac; }
.progress-pill.active { background: #1e3a5f; color: #93c5fd; }
.progress-pill.todo   { background: #1e293b; color: #475569; }
</style>
"""


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def flag(team: Optional[str]) -> str:
    return FLAG_EMOJI.get(team or "", "🏳️")


def conf_color(team: Optional[str]) -> str:
    conf = CONFEDERATION.get(team or "", "")
    return CONFEDERATION_COLORS.get(conf, "#64748b")


def round_css_class(round_name: str) -> str:
    return {
        "Round of 32":   "r32",
        "Round of 16":   "r16",
        "Quarter-Final": "qf",
        "Semi-Final":    "sf",
        "Final":         "final",
        "Third Place":   "tp",
    }.get(round_name, "r32")


def _round_header(round_name: str, n_matches: int) -> str:
    color = ROUND_ACCENT.get(round_name, "#64748b")
    return f"""
    <div class="round-header">
      <div class="round-dot" style="background:{color}"></div>
      <span class="round-label">{round_name}</span>
      <span class="round-count">{n_matches} match{'es' if n_matches != 1 else ''}</span>
    </div>"""


def _champion_banner(team: str) -> str:
    f = flag(team)
    return f"""
    <div class="champion-banner">
      <div class="champion-label">🏆 &nbsp; YOUR PREDICTED CHAMPION</div>
      <div class="champion-name">{f} {team}</div>
    </div>"""


# ─────────────────────────────────────────────────────────────────
# MANUAL BRACKET (USER PICKS ONLY)
# ─────────────────────────────────────────────────────────────────

def _get_group_qualified(group_df: pd.DataFrame) -> Tuple[Dict, Dict, List]:
    """
    Extract most likely winner, runner-up, and best 8 thirds from
    group_stage_summary.csv for the starting bracket state.
    Falls back to FIFA rank order if CSV unavailable.
    """
    winners:    Dict[str, str] = {}
    runners_up: Dict[str, str] = {}
    thirds_raw: List[Dict]     = []

    if group_df.empty:
        # Fallback: use group order as-is
        for gname, teams in groups.items():
            letter = gname.replace("Group ", "")
            ranked = sorted(teams, key=lambda t: FIFA_2026_RANK.get(t, 99))
            winners[letter]    = ranked[0]
            runners_up[letter] = ranked[1]
            thirds_raw.append({
                "team": ranked[2],
                "points": 0,
                "gd": 0,
                "group": letter,
            })
    else:
        for gname, teams in groups.items():
            letter = gname.replace("Group ", "")
            gdf = group_df[group_df["Group"] == gname].copy() if "Group" in group_df.columns else pd.DataFrame()

            if gdf.empty:
                ranked = sorted(teams, key=lambda t: FIFA_2026_RANK.get(t, 99))
                winners[letter]    = ranked[0]
                runners_up[letter] = ranked[1]
                thirds_raw.append({"team": ranked[2], "points": 0, "gd": 0, "group": letter})
            else:
                sort_col = "1st_Place_Prob" if "1st_Place_Prob" in gdf.columns else "Advance_Prob"
                gdf_sorted = gdf.sort_values(sort_col, ascending=False)
                team_list = gdf_sorted["Team"].tolist() if "Team" in gdf_sorted.columns else teams
                if len(team_list) >= 2:
                    winners[letter]    = team_list[0]
                    runners_up[letter] = team_list[1]
                if len(team_list) >= 3:
                    thirds_raw.append({
                        "team":   team_list[2],
                        "points": float(gdf_sorted.iloc[2].get("Advance_Prob", 0)),
                        "gd":     0,
                        "group":  letter,
                    })

    # Rank thirds and take best 8
    thirds_sorted = sorted(thirds_raw, key=lambda x: x["points"], reverse=True)[:8]
    best_8 = [t["team"] for t in thirds_sorted]

    return winners, runners_up, best_8


def render_manual_bracket():
    """Render the interactive manual bracket with pick dropdowns."""
    st.markdown("""
    <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;
                padding:1rem 1.25rem;margin-bottom:1rem;'>
      <div style='color:#94a3b8;font-size:0.85rem;'>
         <strong>Make your predictions!</strong> Pick the winner of each match. 
        The bracket updates automatically — your picks cascade into later rounds.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Session state init ────────────────────────────────────────
    if "manual_picks" not in st.session_state:
        st.session_state.manual_picks = {}
    if "manual_r32" not in st.session_state:
        # Build initial R32 from group data
        group_df = bracket_service.group_df
        winners, runners_up, best_8 = _get_group_qualified(group_df)
        from services.bracket_service import build_r32_bracket
        r32 = build_r32_bracket(winners, runners_up, best_8)
        st.session_state.manual_r32 = r32
        st.session_state.manual_winners    = winners
        st.session_state.manual_runners_up = runners_up
        st.session_state.manual_best_8     = best_8

    picks = st.session_state.manual_picks
    r32   = st.session_state.manual_r32

    # ── Progress tracker ──────────────────────────────────────────
    r32_done = sum(1 for mid in range(73, 89) if picks.get(mid))
    r16_done = sum(1 for mid in range(89, 97) if picks.get(mid))
    qf_done  = sum(1 for mid in range(97, 101) if picks.get(mid))
    sf_done  = sum(1 for mid in range(101, 103) if picks.get(mid))
    fin_done = 1 if picks.get(103) else 0

    stages = [
        ("Round of 32", r32_done, 16),
        ("Round of 16", r16_done, 8),
        ("Quarter-Final", qf_done, 4),
        ("Semi-Final", sf_done, 2),
        ("Final", fin_done, 1),
    ]
    pills_html = '<div class="progress-row">'
    for label, done, total in stages:
        cls = "done" if done == total else ("active" if done > 0 else "todo")
        pills_html += f'<span class="progress-pill {cls}">{label} {done}/{total}</span>'
    pills_html += "</div>"
    st.markdown(pills_html, unsafe_allow_html=True)

    # ── Reset and Save/Load buttons ──────────────────────────────
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    with col1:
        if st.button("💾 Save My Bracket", use_container_width=True):
            save_user_bracket()
            st.success("Bracket saved successfully!")
    with col2:
        if st.button("📂 Load Saved Bracket", use_container_width=True):
            load_user_bracket()
            st.rerun()
    with col3:
        if st.button("🔄 Reset All", use_container_width=True):
            st.session_state.manual_picks = {}
            st.rerun()

    #  Cascade bracket state from current picks 
    cascade_state = cascade_bracket(picks, bracket_service.matchup_df)

    # Render rounds
    def get_teams_for_match(match_id: int) -> Tuple[Optional[str], Optional[str]]:
        """Get the two teams for any match from cascade state or R32."""
        if match_id in r32:
            return r32[match_id]
        cs = cascade_state.get(match_id, {})
        return cs.get("team1"), cs.get("team2")

    def render_pick_match(
        match_id: int,
        round_name: str,
        container,
    ):
        """Render one pickable match card inside a Streamlit container."""
        t1, t2 = get_teams_for_match(match_id)

        if not t1 and not t2:
            container.markdown(
                f'<div class="match-card {round_css_class(round_name)}">'
                f'<div class="match-id">M{match_id}</div>'
                f'<div style="color:#475569;font-size:0.8rem;">Awaiting previous round</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            return

        # Head-to-head probabilities
        probs = None
        if t1 and t2:
            probs = bracket_service.get_matchup(t1, t2)

        current_pick = picks.get(match_id)

        # Match header card
        prob_bar = ""
        if probs:
            hw, dr, aw = probs["home_win"], probs["draw"], probs["away_win"]
            prob_bar = f"""
            <div class="prob-bar-wrap" style="margin-top:0.4rem">
              <div class="prob-bar-labels">
                <span>{flag(t1)} {hw:.0f}%</span>
                <span>Draw {dr:.0f}%</span>
                <span>{aw:.0f}% {flag(t2)}</span>
              </div>
              <div class="prob-bar-bg">
                <div class="prob-bar-home" style="width:{hw}%"></div>
                <div class="prob-bar-draw" style="width:{dr}%"></div>
                <div class="prob-bar-away" style="width:{aw}%"></div>
              </div>
            </div>"""

        winner_html = ""
        if current_pick:
            loser = t2 if current_pick == t1 else t1
            winner_html = f"""
            <div style="margin-top:0.4rem;font-size:0.8rem;">
              <span style="color:#f59e0b;font-weight:600;">✓ {flag(current_pick)} {current_pick}</span>
              &nbsp;
              <span style="color:#475569;text-decoration:line-through;">{flag(loser)} {loser}</span>
            </div>"""

        container.markdown(
            f'<div class="match-card {round_css_class(round_name)}">'
            f'<div class="match-id">M{match_id} · {round_name}</div>'
            f'<div style="font-size:0.9rem;font-weight:500;color:#e2e8f0;margin:0.3rem 0;">'
            f'{flag(t1)} {t1 or "TBD"}  vs  {flag(t2)} {t2 or "TBD"}'
            f'</div>'
            f'{prob_bar}'
            f'{winner_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        if t1 and t2:
            options = ["— pick winner —", t1, t2]
            default_idx = 0
            if current_pick == t1:
                default_idx = 1
            elif current_pick == t2:
                default_idx = 2

            choice = container.selectbox(
                label       = f"M{match_id}",
                options     = options,
                index       = default_idx,
                label_visibility = "collapsed",
                key         = f"pick_{match_id}",
            )

            if choice != "— pick winner —" and choice != current_pick:
                st.session_state.manual_picks[match_id] = choice
                st.rerun()

    #  Layout: stacked rounds 
    for round_name in ROUND_DISPLAY_ORDER:
        match_ids = sorted(BRACKET_ROUNDS.get(round_name, []))
        if not match_ids:
            continue

        st.markdown(_round_header(round_name, len(match_ids)), unsafe_allow_html=True)

        # Responsive columns — fewer matches = wider cards
        n_cols = min(len(match_ids), 8)
        cols = st.columns(n_cols)

        for idx, mid in enumerate(match_ids):
            col = cols[idx % n_cols]
            render_pick_match(mid, round_name, col)

        st.divider()

    #  Champion reveal 
    champion = picks.get(FINAL_MATCH)
    if champion:
        st.markdown(_champion_banner(champion), unsafe_allow_html=True)
        st.balloons()
    else:
        remaining = 16 - sum(1 for mid in range(73, 89) if picks.get(mid))
        if remaining > 0:
            st.markdown(
                f'<div style="text-align:center;color:#475569;padding:2rem;">'
                f' Make your picks! {remaining} match{"es" if remaining != 1 else ""} remaining in Round of 32</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("👆 Continue picking winners in the rounds above to determine your champion!")

    # Sidebar: picks summary
    with st.sidebar:
        st.markdown("### 🖊️ Your Picks Summary")
        if not picks:
            st.caption("No picks yet — start with Round of 32 above")
        else:
            # Group picks by round
            picks_by_round = {r: [] for r in ROUND_DISPLAY_ORDER}
            for mid in sorted(picks):
                winner = picks[mid]
                for r, mids in BRACKET_ROUNDS.items():
                    if mid in mids:
                        picks_by_round[r].append((mid, winner))
                        break
            
            for round_name in ROUND_DISPLAY_ORDER:
                if picks_by_round[round_name]:
                    st.markdown(f"**{round_name}**")
                    for mid, winner in picks_by_round[round_name][:3]:  # Show first 3
                        st.markdown(f"• M{mid}: {flag(winner)} {winner}")
                    if len(picks_by_round[round_name]) > 3:
                        st.caption(f"+{len(picks_by_round[round_name]) - 3} more")
                    st.markdown("---")


def save_user_bracket():
    """Save user predictions to session state (persisted in browser session)"""
    import json
    # Store in session state for potential export
    if "manual_picks" in st.session_state:
        st.session_state.saved_picks = st.session_state.manual_picks.copy()


def load_user_bracket():
    """Load user predictions from saved session state"""
    if "saved_picks" in st.session_state and st.session_state.saved_picks:
        st.session_state.manual_picks = st.session_state.saved_picks.copy()


# MATCH DETAIL PANEL 

def render_matchup_lookup():
    """Quick head-to-head lookup in the sidebar."""
    from config.tournament_config import ALL_TEAMS
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Match Predictor")
    st.sidebar.markdown("*AI-powered matchup probabilities*")

    all_teams = sorted(ALL_TEAMS)
    h = st.sidebar.selectbox("Home team", all_teams, key="lookup_home")
    a = st.sidebar.selectbox("Away team", all_teams, key="lookup_away", index=1)

    if h == a:
        st.sidebar.warning("Pick two different teams")
        return

    probs = bracket_service.get_matchup(h, a)
    if probs is None:
        st.sidebar.error("No data found for this matchup")
        return

    hw, dr, aw = probs["home_win"], probs["draw"], probs["away_win"]
    hg, ag     = probs["home_goals"], probs["away_goals"]

    st.sidebar.markdown(f"""
    <div class="info-panel">
      <h4>{flag(h)} {h} vs {flag(a)} {a}</h4>
      <div class="stat-row">
        <span class="stat-label">{h} win</span>
        <span class="stat-value gold">{hw:.1f}%</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Draw</span>
        <span class="stat-value">{dr:.1f}%</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">{a} win</span>
        <span class="stat-value">{aw:.1f}%</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">xG {h}</span>
        <span class="stat-value">{hg:.2f}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">xG {a}</span>
        <span class="stat-value">{ag:.2f}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_bracket_page():
    """Main entry point - renders ONLY the user bracket (no AI tab)"""
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="mode-header">
      <p class="mode-title">🏆 WC 2026 Interactive Bracket</p>
      <p class="mode-subtitle">
        Make your own tournament predictions! Pick winners in each match and watch your bracket come to life.
        No AI predictions — you're in full control.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Directly render manual bracket 
    render_manual_bracket()

    # Shared matchup lookup in sidebar
    render_matchup_lookup()
# frontend/bracket_page.py (ADD THIS FUNCTION)

def render_complete_bracket(results: Dict, title: str = "Tournament Bracket"):
    """
    Render a complete bracket with all scores
    results: Dict[match_id, {"team1", "team2", "score", "winner"}]
    """
    
    st.markdown(f"### {title}")
    
    # Define rounds in order
    rounds = [
        ("Round of 32", 73, 88, 8),      # (name, start_id, end_id, columns)
        ("Round of 16", 89, 96, 4),
        ("Quarter-Final", 97, 100, 2),
        ("Semi-Final", 101, 102, 2),
        ("Final", 103, 103, 1)
    ]
    
    for round_name, start_id, end_id, num_cols in rounds:
        st.markdown(f"#### {round_name}")
        
        # Get matches for this round
        matches = []
        for mid in range(start_id, end_id + 1):
            if mid in results:
                matches.append(results[mid])
        
        if matches:
            cols = st.columns(min(num_cols, len(matches)))
            for idx, match in enumerate(matches):
                with cols[idx % len(cols)]:
                    # Winner highlight
                    winner_style = "color: #f59e0b; font-weight: bold;"
                    loser_style = "color: #64748b;"
                    
                    # Determine which team won
                    team1_style = winner_style if match['winner'] == match['team1'] else loser_style
                    team2_style = winner_style if match['winner'] == match['team2'] else loser_style
                    
                    # Penalty indicator
                    penalty_badge = ""
                    if match.get('is_penalties'):
                        penalty_badge = "<span style='font-size:0.7rem; color:#f59e0b;'>(P)</span>"
                    
                    st.markdown(f"""
                    <div style="background: #0f172a; border: 1px solid #1e293b; 
                                border-radius: 10px; padding: 0.75rem; margin: 0.5rem 0;">
                        <div style="font-size: 0.7rem; color: #475569;">Match {match.get('match_id', '?')}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin: 0.5rem 0;">
                            <span style="{team1_style}">{match['team1']}</span>
                            <span style="font-family: monospace; font-weight: bold; color: #f59e0b;">
                                {match['score']}
                            </span>
                            <span style="{team2_style}">{match['team2']}</span>
                        </div>
                        <div style="border-top: 1px solid #1e293b; margin: 0.5rem 0;"></div>
                        <div style="font-size: 0.75rem; color: #10b981;">
                            🏆 Winner: {match['winner']} {penalty_badge}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
    
    # Show champion
    final_match = results.get(103)
    if final_match:
        champion = final_match['winner']
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1c1400 0%, #2d1f00 100%);
                    border: 2px solid #f59e0b;
                    border-radius: 16px; 
                    padding: 2rem; 
                    text-align: center;
                    margin-top: 1rem;">
            <div style="font-size: 0.8rem; letter-spacing: 0.3em; color: #b45309;">🏆 WORLD CUP 2026 CHAMPION 🏆</div>
            <div style="font-size: 3rem; font-weight: bold; color: #f59e0b; margin: 0.5rem 0;">
                {champion}
            </div>
            <div style="color: #92400e; font-size: 0.85rem;">
                Defeated {final_match['team2'] if final_match['winner'] == final_match['team1'] else final_match['team1']} in the final
            </div>
        </div>
        """, unsafe_allow_html=True)