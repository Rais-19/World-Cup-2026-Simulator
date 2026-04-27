import streamlit as st
import pandas as pd
import random
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.bracket_service import bracket_service, cascade_bracket

R16_FEEDERS = {
    89: (74, 77),
    90: (73, 75),
    91: (76, 78),
    92: (79, 80),
    93: (83, 84),
    94: (81, 82),
    95: (86, 88),
    96: (85, 87),
}
QF_FEEDERS = {
    97:  (89, 90),
    98:  (93, 94),
    99:  (91, 92),
    100: (95, 96),
}
SF_FEEDERS = {
    101: (97, 98),
    102: (99, 100),
}
FINAL_ID       = 103
THIRD_PLACE_ID = 104

# FLAG EMOJIS
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

def flag(team: str) -> str:
    return FLAG_EMOJI.get(team or "", "🏳️")

# DATA LOADING

@st.cache_data
def load_matchup_data() -> pd.DataFrame:
    data_dir = Path(__file__).parent.parent / "data"
    return pd.read_csv(data_dir / "matchup_probabilities.csv")


@st.cache_data
def load_r32_teams() -> Dict[int, Tuple[str, str]]:
    """
    Load ONLY Round of 32 teams from CSV.
    Returns {match_id: (team1, team2)} for matches 73-88 ONLY.
    All later rounds are determined dynamically by simulation results.
    This is the core fix — we never load R16/QF/SF/Final from the CSV.
    """
    data_dir = Path(__file__).parent.parent / "data"
    df = pd.read_csv(data_dir / "knockout_bracket.csv")
    r32_df = df[df["Round"] == "Round of 32"]
    result = {}
    for _, row in r32_df.iterrows():
        mid = int(row["Match_ID"])
        result[mid] = (str(row["Team1"]), str(row["Team2"]))
    return result

# SCENARIO CONFIG
SCENARIOS = {
    "Most Likely (Default)": {
        "modifier": 0,
        "deterministic": True,
        "description": "Based purely on team strengths. Same outcome every time.",
    },
    "Giant Killers (Upsets)": {
        "modifier": 18,
        "deterministic": False,
        "description": "Underdogs overperform. Expect Cinderella stories. Different each click!",
    },
    "European Dominance": {
        "modifier": -12,
        "deterministic": False,
        "description": "European teams show their strength. Favorites usually win. Different each click!",
    },
    "South American Revival": {
        "modifier": 12,
        "deterministic": False,
        "description": "South American teams surge. Brazil/Argentina fired up. Different each click!",
    },
    "Home Advantage": {
        "modifier": 10,
        "deterministic": False,
        "description": "North American teams get a boost from home crowds. Different each click!",
    },
    "Golden Generation": {
        "modifier": -8,
        "deterministic": False,
        "description": "Star players peak at the right moment. Slight favorites edge. Different each click!",
    },
}

ELO_FALLBACK = {
    "Spain": 1850, "France": 1840, "Argentina": 1835, "Brazil": 1825,
    "Germany": 1800, "England": 1790, "Portugal": 1780, "Netherlands": 1775,
    "Belgium": 1760, "Croatia": 1740, "Uruguay": 1720, "Colombia": 1710,
    "Morocco": 1680, "United States": 1660, "Japan": 1650, "Mexico": 1640,
    "Senegal": 1630, "Switzerland": 1625, "Iran": 1600, "South Korea": 1590,
    "Australia": 1580, "Austria": 1570, "Ecuador": 1560, "Turkey": 1550,
    "Sweden": 1545, "Norway": 1540, "Algeria": 1520, "Egypt": 1515,
    "Czech Republic": 1510, "Qatar": 1500, "Scotland": 1495, "Canada": 1490,
    "Ivory Coast": 1480, "Tunisia": 1470, "Paraguay": 1450, "Saudi Arabia": 1440,
    "DR Congo": 1430, "Ghana": 1420, "Bosnia and Herzegovina": 1410,
    "South Africa": 1400, "Jordan": 1390, "Cape Verde": 1385, "Iraq": 1380,
    "Uzbekistan": 1370, "Panama": 1360, "New Zealand": 1350, "Haiti": 1340,
    "Curaçao": 1330,
}

def get_elo(team: str) -> float:
    try:
        from services.prediction_service import prediction_service
        return prediction_service.get_team_elo(team)
    except Exception:
        return ELO_FALLBACK.get(team, 1500)

# MATCH SIMULATION

def simulate_match(
    team1: str,
    team2: str,
    matchup_df: pd.DataFrame,
    modifier: float = 0,
    strength: float = 1.0,
) -> Dict:
    """Simulate one match. Winner is ALWAYS team1 or team2."""

    # Look up probabilities
    row = matchup_df[
        (matchup_df["Home"] == team1) & (matchup_df["Away"] == team2)
    ]
    swapped = False
    if row.empty:
        row = matchup_df[
            (matchup_df["Home"] == team2) & (matchup_df["Away"] == team1)
        ]
        swapped = True

    if not row.empty:
        r = row.iloc[0]
        if swapped:
            home_win = float(r["Away_Win_Prob"])
            away_win = float(r["Home_Win_Prob"])
            draw     = float(r["Draw_Prob"])
            xg1      = float(r["Expected_Away_Goals"])
            xg2      = float(r["Expected_Home_Goals"])
        else:
            home_win = float(r["Home_Win_Prob"])
            away_win = float(r["Away_Win_Prob"])
            draw     = float(r["Draw_Prob"])
            xg1      = float(r["Expected_Home_Goals"])
            xg2      = float(r["Expected_Away_Goals"])
    else:
        # Elo fallback
        e1 = get_elo(team1)
        e2 = get_elo(team2)
        p1 = 1 / (1 + 10 ** ((e2 - e1) / 400))
        home_win = p1 * 80
        away_win = (1 - p1) * 80
        draw = 20.0
        xg1 = xg2 = 1.3

    # Apply scenario modifier
    if modifier != 0 and strength > 0:
        adj = modifier * strength
        if home_win > away_win:         # team1 is favorite → boost underdog (team2)
            home_win = max(5.0, home_win - adj)
            away_win = min(85.0, away_win + adj)
        else:                           # team2 is favorite → boost underdog (team1)
            home_win = min(85.0, home_win + adj)
            away_win = max(5.0, away_win - adj)
        draw = max(0.0, 100.0 - home_win - away_win)

    total = home_win + draw + away_win
    if total <= 0:
        home_win, draw, away_win, total = 40.0, 20.0, 40.0, 100.0

    # Simulate
    r = random.random() * total

    if r < home_win:
        winner = team1
        g1 = max(1, round(random.gauss(xg1, 1.1)))
        g2 = max(0, round(random.gauss(xg2, 0.9)))
        if g1 <= g2:
            g1 = g2 + random.randint(1, 2)
        is_penalties = False

    elif r < home_win + draw:
        g = max(1, round(random.gauss((xg1 + xg2) / 2, 0.8)))
        g1 = g2 = g
        e1, e2 = get_elo(team1), get_elo(team2)
        p1_pen = max(0.35, min(0.65, 0.5 + (e1 - e2) / 800))
        winner = team1 if random.random() < p1_pen else team2
        is_penalties = True

    else:
        winner = team2
        g2 = max(1, round(random.gauss(xg2, 1.1)))
        g1 = max(0, round(random.gauss(xg1, 0.9)))
        if g2 <= g1:
            g2 = g1 + random.randint(1, 2)
        is_penalties = False

    g1, g2 = min(g1, 7), min(g2, 7)

    # Safety guard
    if winner not in (team1, team2):
        winner = team1 if random.random() < 0.5 else team2

    return {
        "team1": team1, "team2": team2,
        "score": f"{g1} - {g2}",
        "winner": winner,
        "is_penalties": is_penalties,
    }
# FULL TOURNAMENT SIMULATION 


@st.cache_data
def load_most_likely_bracket() -> Dict[int, Dict]:
    """Reads the pre-computed CSV. Cached — never changes."""
    data_dir = Path(__file__).parent.parent / "data"
    df = pd.read_csv(data_dir / "knockout_bracket.csv")
    bracket = {}
    for _, row in df.iterrows():
        mid    = int(row["Match_ID"])
        team1  = str(row["Team1"])
        team2  = str(row["Team2"])
        winner = str(row["Most_Likely_Winner"])
        if winner not in (team1, team2):
            winner = team1
        bracket[mid] = {
            "match_id":     mid,
            "round":        str(row["Round"]),
            "team1":        team1,
            "team2":        team2,
            "winner":       winner,
            "score":        f"({row['Probability']:.0f}% likely)",
            "is_penalties": False,
        }
    return bracket
def simulate_full_tournament(
    scenario_name: str,
    r32_teams: Dict[int, Tuple[str, str]],
    matchup_df: pd.DataFrame,
    strength: float = 1.0,
) -> Dict[int, Dict]:
    if scenario_name == "Most Likely (Default)":
        return load_most_likely_bracket()  
    cfg      = SCENARIOS[scenario_name]
    modifier = cfg["modifier"]

    if cfg["deterministic"]:
        random.seed(42)
    else:
        random.seed(int(time.time() * 1000) % 10_000_000)

    results: Dict[int, Dict] = {}
    winners: Dict[int, str]  = {}

    def play(mid: int, t1: str, t2: str, round_name: str) -> str:
        res = simulate_match(t1, t2, matchup_df, modifier, strength)
        res["match_id"] = mid
        res["round"]    = round_name
        results[mid]    = res
        winners[mid]    = res["winner"]
        return res["winner"]

    # Round of 32 — teams from CSV
    for mid in sorted(r32_teams.keys()):
        t1, t2 = r32_teams[mid]
        play(mid, t1, t2, "Round of 32")

    # Round of 16 — teams = winners of R32 matches
    for mid, (f1, f2) in sorted(R16_FEEDERS.items()):
        t1, t2 = winners.get(f1), winners.get(f2)
        if t1 and t2:
            play(mid, t1, t2, "Round of 16")

    # Quarter-Finals — teams = winners of R16 matches
    for mid, (f1, f2) in sorted(QF_FEEDERS.items()):
        t1, t2 = winners.get(f1), winners.get(f2)
        if t1 and t2:
            play(mid, t1, t2, "Quarter-Final")

    # Semi-Finals — teams = winners of QF matches
    sf_losers: List[str] = []
    for mid, (f1, f2) in sorted(SF_FEEDERS.items()):
        t1, t2 = winners.get(f1), winners.get(f2)
        if t1 and t2:
            w = play(mid, t1, t2, "Semi-Final")
            sf_losers.append(t2 if w == t1 else t1)

    # Third Place — the TWO SF losers
    if len(sf_losers) == 2:
        play(THIRD_PLACE_ID, sf_losers[0], sf_losers[1], "Third Place")

    # Final — winners of the two SFs
    t1, t2 = winners.get(101), winners.get(102)
    if t1 and t2:
        play(FINAL_ID, t1, t2, "Final")

    return results

# SINGLE MATCH REGENERATION 

def regenerate_from_match(
    results: Dict[int, Dict],
    match_id: int,
    r32_teams: Dict[int, Tuple[str, str]],
    matchup_df: pd.DataFrame,
    scenario_name: str,
    strength: float,
) -> Dict[int, Dict]:
    """Re-simulate match_id and all downstream matches using dynamic cascade."""

    cfg      = SCENARIOS[scenario_name]
    modifier = cfg["modifier"]
    random.seed(int(time.time() * 1000) % 10_000_000)

    results  = dict(results)
    winners  = {mid: r["winner"] for mid, r in results.items()}

    all_ordered = (
        list(range(73, 89)) +
        sorted(R16_FEEDERS.keys()) +
        sorted(QF_FEEDERS.keys()) +
        sorted(SF_FEEDERS.keys()) +
        [THIRD_PLACE_ID, FINAL_ID]
    )

    if match_id not in all_ordered:
        return results

    start_idx = all_ordered.index(match_id)

    for mid in all_ordered[start_idx:]:
        # Determine the two teams for this match
        if mid in r32_teams:
            t1, t2 = r32_teams[mid]
        elif mid in R16_FEEDERS:
            f1, f2 = R16_FEEDERS[mid]
            t1, t2 = winners.get(f1), winners.get(f2)
        elif mid in QF_FEEDERS:
            f1, f2 = QF_FEEDERS[mid]
            t1, t2 = winners.get(f1), winners.get(f2)
        elif mid in SF_FEEDERS:
            f1, f2 = SF_FEEDERS[mid]
            t1, t2 = winners.get(f1), winners.get(f2)
        elif mid == THIRD_PLACE_ID:
            # Always recompute SF losers from current state
            sf_losers = []
            for sf_id in sorted(SF_FEEDERS.keys()):
                if sf_id in results:
                    r = results[sf_id]
                    loser = r["team2"] if r["winner"] == r["team1"] else r["team1"]
                    sf_losers.append(loser)
            if len(sf_losers) < 2:
                continue
            t1, t2 = sf_losers[0], sf_losers[1]
        elif mid == FINAL_ID:
            t1, t2 = winners.get(101), winners.get(102)
        else:
            continue

        if not t1 or not t2:
            continue

        round_name = (
            "Round of 32"   if mid in range(73, 89)   else
            "Round of 16"   if mid in R16_FEEDERS      else
            "Quarter-Final" if mid in QF_FEEDERS        else
            "Semi-Final"    if mid in SF_FEEDERS        else
            "Third Place"   if mid == THIRD_PLACE_ID    else
            "Final"
        )

        res = simulate_match(t1, t2, matchup_df, modifier, strength)
        res["match_id"] = mid
        res["round"]    = round_name
        results[mid]    = res
        winners[mid]    = res["winner"]

    return results

# FAVORITES
# ─────────────────────────────────────────────────────────────────

def _fav_path() -> Path:
    return Path(__file__).parent.parent / "data" / "favorite_brackets.json"

def save_favorite_bracket(results: Dict, scenario_name: str, strength: float) -> str:
    path = _fav_path()
    favorites = json.loads(path.read_text()) if path.exists() else []
    fid = hashlib.md5(f"{time.time()}{scenario_name}{strength}".encode()).hexdigest()[:8]
    favorites.append({
        "id":       fid,
        "scenario": scenario_name,
        "strength": strength,
        "date":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "champion": results.get(FINAL_ID, {}).get("winner", "Unknown"),
        "results":  {str(k): v for k, v in results.items()},
    })
    favorites = favorites[-20:]
    path.write_text(json.dumps(favorites, indent=2))
    return fid

def load_favorites() -> List[Dict]:
    path = _fav_path()
    return json.loads(path.read_text()) if path.exists() else []

# ─────────────────────────────────────────────────────────────────
# BRACKET RENDERER
# ─────────────────────────────────────────────────────────────────

def render_complete_bracket(
    results: Dict,
    title: str,
    show_regenerate: bool = False,
    r32_teams: Dict = None,
    matchup_df: pd.DataFrame = None,
    scenario_name: str = None,
    strength: float = 1.0,
):
    st.markdown(f"### {title}")

    rounds = [
        ("Round of 32",   list(range(73, 89)), 4),
        ("Round of 16",   list(range(89, 97)), 4),
        ("Quarter-Final", list(range(97, 101)), 2),
        ("Semi-Final",    [101, 102],           2),
        ("Final",         [FINAL_ID],           1),
    ]

    for round_name, match_ids, num_cols in rounds:
        matches = [results[mid] for mid in match_ids if mid in results]
        if not matches:
            continue

        st.markdown(f"#### {round_name}")
        cols = st.columns(min(num_cols, len(matches)))

        for idx, match in enumerate(matches):
            mid = match.get("match_id", 0)
            w   = match["winner"]
            t1  = match["team1"]
            t2  = match["team2"]

            t1_style = "color:#f59e0b;font-weight:bold;" if w == t1 else "color:#64748b;"
            t2_style = "color:#f59e0b;font-weight:bold;" if w == t2 else "color:#64748b;"
            pen      = " (P)" if match.get("is_penalties") else ""

            with cols[idx % len(cols)]:
                st.markdown(f"""
                <div style="background:#0f172a;border:1px solid #1e293b;
                            border-radius:10px;padding:0.75rem;margin:0.5rem 0;">
                    <div style="font-size:0.65rem;color:#475569;">
                        M{mid} · {round_name}
                    </div>
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;margin:0.5rem 0;">
                        <span style="{t1_style}">{flag(t1)} {t1}</span>
                        <span style="font-family:monospace;font-weight:bold;
                                     color:#f59e0b;">{match['score']}</span>
                        <span style="{t2_style}">{t2} {flag(t2)}</span>
                    </div>
                    <div style="border-top:1px solid #1e293b;margin:0.5rem 0;"></div>
                    <div style="font-size:0.75rem;color:#10b981;">
                        🏆 {flag(w)} {w}{pen}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if show_regenerate and r32_teams and matchup_df is not None and scenario_name:
                    if st.button("🔄", key=f"regen_{mid}",
                                 help=f"Regenerate M{mid} and cascade forward"):
                        new_results = regenerate_from_match(
                            results, mid, r32_teams,
                            matchup_df, scenario_name, strength
                        )
                        st.session_state.current_results  = new_results
                        st.session_state.current_scenario = scenario_name
                        st.session_state.current_strength = strength
                        st.rerun()

        st.divider()

    # Champion + Third Place banner
    final = results.get(FINAL_ID)
    third = results.get(THIRD_PLACE_ID)

    if final:
        champion  = final["winner"]
        runner_up = final["team2"] if champion == final["team1"] else final["team1"]
        third_line = ""
        if third:
            tw = third["winner"]
            tl = third["team2"] if tw == third["team1"] else third["team1"]
            third_line = (
                f'<div style="margin-top:0.5rem;font-size:0.8rem;color:#92400e;">'
                f'🥉 {flag(tw)} {tw} &nbsp;|&nbsp; 4th: {flag(tl)} {tl}</div>'
            )
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1c1400 0%,#2d1f00 100%);
                    border:2px solid #f59e0b;border-radius:16px;
                    padding:2rem;text-align:center;margin-top:1rem;">
            <div style="font-size:0.75rem;letter-spacing:0.3em;color:#b45309;">
                🏆 &nbsp; WORLD CUP 2026 CHAMPION &nbsp; 🏆
            </div>
            <div style="font-size:3rem;font-weight:bold;color:#f59e0b;margin:0.5rem 0;">
                {flag(champion)} {champion}
            </div>
            <div style="color:#92400e;font-size:0.85rem;">
                defeated {flag(runner_up)} {runner_up} in the final · {final['score']}
            </div>
            {third_line}
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────────────────────────────

def render_scenarios_page():
    st.title("🎲 Alternate Realities")

    # Init session state
    for key, default in [
        ("current_results",  None),
        ("current_scenario", "Most Likely (Default)"),
        ("current_strength", 1.0),
        ("scenario_attempts", {}),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                padding:1.5rem;margin-bottom:1.5rem;">
        <p style="color:#94a3b8;margin:0;font-size:0.9rem;line-height:1.6;">
            🌍 Explore different possible World Cup 2026 timelines.<br>
            • <strong>Most Likely</strong> — same outcome every time<br>
            • <strong>Other scenarios</strong> — random, different every click<br>
            • Adjust <strong>Strength</strong> to control how extreme the effect is<br>
            • Click <strong>🔄</strong> on any match to re-roll it and cascade forward
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Load data — r32_teams is the ONLY thing we read from the CSV
    matchup_df = load_matchup_data()
    r32_teams  = load_r32_teams()

    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    scenario_names = list(SCENARIOS.keys())

    with col1:
        selected_scenario = st.selectbox(
            "Choose a timeline:",
            scenario_names,
            index=scenario_names.index(st.session_state.current_scenario),
        )

    is_deterministic = SCENARIOS[selected_scenario]["deterministic"]

    with col2:
        strength = st.slider(
            "🎚️ Strength",
            min_value=0.0, max_value=2.0,
            value=st.session_state.current_strength,
            step=0.1,
            disabled=is_deterministic,
            help="0 = no effect · 1 = normal · 2 = extreme",
        )

    with col3:
        if st.button("🎲 SURPRISE ME!", use_container_width=True):
            surprise = random.choice([s for s in scenario_names if not SCENARIOS[s]["deterministic"]])
            st.session_state.current_scenario = surprise
            st.rerun()

    st.info(f"💡 {SCENARIOS[selected_scenario]['description']}")

    if not is_deterministic:
        count = st.session_state.scenario_attempts.get(selected_scenario, 0)
        st.caption(f"🎲 Attempt #{count + 1} — each click gives a different outcome!")

    btn_label = "🎲 GENERATE NEW REALITY" if not is_deterministic else "✅ SHOW MOST LIKELY OUTCOME"
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        simulate_clicked = st.button(btn_label, use_container_width=True, type="primary")

    if simulate_clicked:
        if not is_deterministic:
            st.session_state.scenario_attempts[selected_scenario] = \
                st.session_state.scenario_attempts.get(selected_scenario, 0) + 1

        with st.spinner(f"Simulating {selected_scenario}..."):
            results = simulate_full_tournament(
                selected_scenario, r32_teams, matchup_df, strength
            )

        # Integrity check before storing
        final   = results.get(FINAL_ID, {})
        champion = final.get("winner")
        sf1_w   = results.get(101, {}).get("winner")
        sf2_w   = results.get(102, {}).get("winner")

        if champion and champion not in (sf1_w, sf2_w):
            st.error(
                f"⚠️ Bracket error detected: {champion} is in the final "
                f"but did not win a semi-final. Please click Generate again."
            )
        else:
            st.session_state.current_results  = results
            st.session_state.current_scenario = selected_scenario
            st.session_state.current_strength = strength
            st.rerun()

    # Render bracket if we have results
    if st.session_state.current_results:
        render_complete_bracket(
            st.session_state.current_results,
            f"🏆 {st.session_state.current_scenario}",
            show_regenerate=True,
            r32_teams=r32_teams,
            matchup_df=matchup_df,
            scenario_name=st.session_state.current_scenario,
            strength=st.session_state.current_strength,
        )

        # Save favorite
        _, save_col, _ = st.columns([1, 2, 1])
        with save_col:
            if st.button("💾 SAVE THIS TIMELINE TO FAVORITES", use_container_width=True):
                fid = save_favorite_bracket(
                    st.session_state.current_results,
                    st.session_state.current_scenario,
                    st.session_state.current_strength,
                )
                st.success(f"✅ Saved! ID: {fid}")

    # Saved favorites
    st.markdown("---")
    st.markdown("### ⭐ Saved Timelines")
    favorites = load_favorites()

    if not favorites:
        st.caption("No saved timelines yet.")
    else:
        for fav in reversed(favorites[-10:]):
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(
                    f"**{fav['scenario']}** (strength {fav['strength']}) — "
                    f"Champion: {flag(fav['champion'])} **{fav['champion']}** · {fav['date']}"
                )
            with c2:
                if st.button("Load", key=f"load_{fav['id']}"):
                    st.session_state.current_results  = {int(k): v for k, v in fav["results"].items()}
                    st.session_state.current_scenario = fav["scenario"]
                    st.session_state.current_strength = fav["strength"]
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"del_{fav['id']}"):
                    path = _fav_path()
                    favs = [f for f in load_favorites() if f["id"] != fav["id"]]
                    path.write_text(json.dumps(favs, indent=2))
                    st.rerun()


if __name__ == "__main__":
    render_scenarios_page()