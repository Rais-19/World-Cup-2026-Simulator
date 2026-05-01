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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# BRACKET WIRING
R16_FEEDERS = {
    89: (74, 77), 90: (73, 75), 91: (76, 78), 92: (79, 80),
    93: (83, 84), 94: (81, 82), 95: (86, 88), 96: (85, 87),
}
QF_FEEDERS  = {97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96)}
SF_FEEDERS  = {101: (97, 98), 102: (99, 100)}
FINAL_ID       = 103
THIRD_PLACE_ID = 104

# FLAGS

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

@st.cache_data
def load_r32_from_df(knockout_df: pd.DataFrame) -> Dict[int, Tuple[str, str]]:
    """Extract R32 teams from the already-loaded knockout_df."""
    result = {}
    for _, row in knockout_df[knockout_df["Round"] == "Round of 32"].iterrows():
        result[int(row["Match_ID"])] = (str(row["Team1"]), str(row["Team2"]))
    return result


@st.cache_data
def load_most_likely_from_df(knockout_df: pd.DataFrame) -> Dict[int, Dict]:
    """Build Most Likely bracket from the already-loaded knockout_df. Cached forever."""
    bracket = {}
    for _, row in knockout_df.iterrows():
        mid, team1, team2 = int(row["Match_ID"]), str(row["Team1"]), str(row["Team2"])
        winner = str(row["Most_Likely_Winner"])
        if winner not in (team1, team2):
            winner = team1
        bracket[mid] = {
            "match_id": mid, "round": str(row["Round"]),
            "team1": team1, "team2": team2, "winner": winner,
            "score": f"({row['Probability']:.0f}% likely)", "is_penalties": False,
        }
    return bracket

# SCENARIO CONFIG

SCENARIOS = {
    "Most Likely (Default)":  {"modifier": 0,   "deterministic": True,  "description": "Based purely on team strengths. Same outcome every time."},
    "Giant Killers (Upsets)": {"modifier": 18,  "deterministic": False, "description": "Underdogs overperform. Expect Cinderella stories. Different each click!"},
    "European Dominance":     {"modifier": -12, "deterministic": False, "description": "European teams show their strength. Different each click!"},
    "South American Revival": {"modifier": 12,  "deterministic": False, "description": "South American teams surge. Different each click!"},
    "Home Advantage":         {"modifier": 10,  "deterministic": False, "description": "North American teams get a boost from home crowds. Different each click!"},
    "Golden Generation":      {"modifier": -8,  "deterministic": False, "description": "Star players peak at the right moment. Different each click!"},
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
    "Uzbekistan": 1370, "Panama": 1360, "New Zealand": 1350, "Haiti": 1340, "Curaçao": 1330,
}

def get_elo(team: str) -> float:
    try:
        from services.prediction_service import prediction_service
        return prediction_service.get_team_elo(team)
    except Exception:
        return ELO_FALLBACK.get(team, 1500)

# MATCH SIMULATION

def simulate_match(team1: str, team2: str, matchup_df: pd.DataFrame,
                   modifier: float = 0, strength: float = 1.0) -> Dict:
    row = matchup_df[(matchup_df["Home"] == team1) & (matchup_df["Away"] == team2)]
    swapped = False
    if row.empty:
        row = matchup_df[(matchup_df["Home"] == team2) & (matchup_df["Away"] == team1)]
        swapped = True

    if not row.empty:
        r = row.iloc[0]
        home_win = float(r["Away_Win_Prob"] if swapped else r["Home_Win_Prob"])
        away_win = float(r["Home_Win_Prob"] if swapped else r["Away_Win_Prob"])
        draw     = float(r["Draw_Prob"])
        xg1      = float(r["Expected_Away_Goals"] if swapped else r["Expected_Home_Goals"])
        xg2      = float(r["Expected_Home_Goals"] if swapped else r["Expected_Away_Goals"])
    else:
        e1, e2 = get_elo(team1), get_elo(team2)
        p1 = 1 / (1 + 10 ** ((e2 - e1) / 400))
        home_win, away_win, draw, xg1, xg2 = p1 * 80, (1 - p1) * 80, 20.0, 1.3, 1.3

    if modifier != 0 and strength > 0:
        adj = modifier * strength
        if home_win > away_win:
            home_win = max(5.0, home_win - adj); away_win = min(85.0, away_win + adj)
        else:
            home_win = min(85.0, home_win + adj); away_win = max(5.0, away_win - adj)
        draw = max(0.0, 100.0 - home_win - away_win)

    total = home_win + draw + away_win or 100.0
    r = random.random() * total

    if r < home_win:
        winner, is_penalties = team1, False
        g1 = max(1, round(random.gauss(xg1, 1.1)))
        g2 = max(0, round(random.gauss(xg2, 0.9)))
        if g1 <= g2: g1 = g2 + random.randint(1, 2)
    elif r < home_win + draw:
        g = max(1, round(random.gauss((xg1 + xg2) / 2, 0.8)))
        g1 = g2 = g
        p1p = max(0.35, min(0.65, 0.5 + (get_elo(team1) - get_elo(team2)) / 800))
        winner, is_penalties = (team1 if random.random() < p1p else team2), True
    else:
        winner, is_penalties = team2, False
        g2 = max(1, round(random.gauss(xg2, 1.1)))
        g1 = max(0, round(random.gauss(xg1, 0.9)))
        if g2 <= g1: g2 = g1 + random.randint(1, 2)

    g1, g2 = min(g1, 7), min(g2, 7)
    if winner not in (team1, team2):
        winner = team1 if random.random() < 0.5 else team2

    return {"team1": team1, "team2": team2, "score": f"{g1} - {g2}",
            "winner": winner, "is_penalties": is_penalties}

# FULL TOURNAMENT SIMULATION

def simulate_full_tournament(
    scenario_name: str,
    r32_teams: Dict[int, Tuple[str, str]],
    matchup_df: pd.DataFrame,
    strength: float = 1.0,
    most_likely_bracket: Dict = None,   # ← must be passed for Most Likely
) -> Dict[int, Dict]:

    # Most Likely: return pre-computed CSV bracket — NEVER simulate
    if scenario_name == "Most Likely (Default)":
        return most_likely_bracket or {}

    modifier = SCENARIOS[scenario_name]["modifier"]
    random.seed(int(time.time() * 1000) % 10_000_000)

    results: Dict[int, Dict] = {}
    winners: Dict[int, str]  = {}

    def play(mid, t1, t2, rname):
        res = simulate_match(t1, t2, matchup_df, modifier, strength)
        res["match_id"] = mid; res["round"] = rname
        results[mid] = res; winners[mid] = res["winner"]
        return res["winner"]

    for mid in sorted(r32_teams): play(mid, *r32_teams[mid], "Round of 32")
    for mid, (f1, f2) in sorted(R16_FEEDERS.items()):
        t1, t2 = winners.get(f1), winners.get(f2)
        if t1 and t2: play(mid, t1, t2, "Round of 16")
    for mid, (f1, f2) in sorted(QF_FEEDERS.items()):
        t1, t2 = winners.get(f1), winners.get(f2)
        if t1 and t2: play(mid, t1, t2, "Quarter-Final")

    sf_losers = []
    for mid, (f1, f2) in sorted(SF_FEEDERS.items()):
        t1, t2 = winners.get(f1), winners.get(f2)
        if t1 and t2:
            w = play(mid, t1, t2, "Semi-Final")
            sf_losers.append(t2 if w == t1 else t1)

    if len(sf_losers) == 2: play(THIRD_PLACE_ID, sf_losers[0], sf_losers[1], "Third Place")
    t1, t2 = winners.get(101), winners.get(102)
    if t1 and t2: play(FINAL_ID, t1, t2, "Final")

    return results

# SINGLE MATCH REGENERATION

def regenerate_from_match(results, match_id, r32_teams, matchup_df, scenario_name, strength):
    modifier = SCENARIOS[scenario_name]["modifier"]
    random.seed(int(time.time() * 1000) % 10_000_000)
    results = dict(results)
    winners = {mid: r["winner"] for mid, r in results.items()}
    all_ordered = (list(range(73, 89)) + sorted(R16_FEEDERS) +
                   sorted(QF_FEEDERS) + sorted(SF_FEEDERS) + [THIRD_PLACE_ID, FINAL_ID])
    if match_id not in all_ordered: return results

    for mid in all_ordered[all_ordered.index(match_id):]:
        if mid in r32_teams:           t1, t2 = r32_teams[mid]
        elif mid in R16_FEEDERS:       t1, t2 = winners.get(R16_FEEDERS[mid][0]), winners.get(R16_FEEDERS[mid][1])
        elif mid in QF_FEEDERS:        t1, t2 = winners.get(QF_FEEDERS[mid][0]),  winners.get(QF_FEEDERS[mid][1])
        elif mid in SF_FEEDERS:        t1, t2 = winners.get(SF_FEEDERS[mid][0]),  winners.get(SF_FEEDERS[mid][1])
        elif mid == THIRD_PLACE_ID:
            losers = [results[s]["team2"] if results[s]["winner"] == results[s]["team1"]
                      else results[s]["team1"] for s in sorted(SF_FEEDERS) if s in results]
            if len(losers) < 2: continue
            t1, t2 = losers[0], losers[1]
        elif mid == FINAL_ID:          t1, t2 = winners.get(101), winners.get(102)
        else: continue

        if not t1 or not t2: continue
        rname = ("Round of 32" if mid in range(73, 89) else "Round of 16" if mid in R16_FEEDERS
                 else "Quarter-Final" if mid in QF_FEEDERS else "Semi-Final" if mid in SF_FEEDERS
                 else "Third Place" if mid == THIRD_PLACE_ID else "Final")
        res = simulate_match(t1, t2, matchup_df, modifier, strength)
        res["match_id"] = mid; res["round"] = rname
        results[mid] = res; winners[mid] = res["winner"]

    return results

# FAVORITES

def _fav_path():
    return Path(__file__).parent.parent / "data" / "favorite_brackets.json"

def save_favorite_bracket(results, scenario_name, strength):
    path = _fav_path()
    favs = json.loads(path.read_text()) if path.exists() else []
    fid = hashlib.md5(f"{time.time()}{scenario_name}{strength}".encode()).hexdigest()[:8]
    favs.append({"id": fid, "scenario": scenario_name, "strength": strength,
                 "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "champion": results.get(FINAL_ID, {}).get("winner", "Unknown"),
                 "results": {str(k): v for k, v in results.items()}})
    path.write_text(json.dumps(favs[-20:], indent=2))
    return fid

def load_favorites():
    path = _fav_path()
    return json.loads(path.read_text()) if path.exists() else []

# BRACKET RENDERER
def render_complete_bracket(results, title, show_regenerate=False,
                             r32_teams=None, matchup_df=None,
                             scenario_name=None, strength=1.0):
    st.markdown(f"### {title}")
    rounds = [("Round of 32", list(range(73, 89)), 4),
              ("Round of 16", list(range(89, 97)), 4),
              ("Quarter-Final", list(range(97, 101)), 2),
              ("Semi-Final", [101, 102], 2),
              ("Final", [FINAL_ID], 1)]

    for round_name, match_ids, num_cols in rounds:
        matches = [results[mid] for mid in match_ids if mid in results]
        if not matches: continue
        st.markdown(f"#### {round_name}")
        cols = st.columns(min(num_cols, len(matches)))
        for idx, match in enumerate(matches):
            mid = match.get("match_id", 0)
            w, t1, t2 = match["winner"], match["team1"], match["team2"]
            t1s = "color:#f59e0b;font-weight:bold;" if w == t1 else "color:#64748b;"
            t2s = "color:#f59e0b;font-weight:bold;" if w == t2 else "color:#64748b;"
            pen = " (P)" if match.get("is_penalties") else ""
            with cols[idx % len(cols)]:
                st.markdown(f"""
                <div style="background:#0f172a;border:1px solid #1e293b;
                            border-radius:10px;padding:0.75rem;margin:0.5rem 0;">
                    <div style="font-size:0.65rem;color:#475569;">M{mid} · {round_name}</div>
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;margin:0.5rem 0;">
                        <span style="{t1s}">{flag(t1)} {t1}</span>
                        <span style="font-family:monospace;font-weight:bold;color:#f59e0b;">
                            {match['score']}</span>
                        <span style="{t2s}">{t2} {flag(t2)}</span>
                    </div>
                    <div style="border-top:1px solid #1e293b;margin:0.5rem 0;"></div>
                    <div style="font-size:0.75rem;color:#10b981;">🏆 {flag(w)} {w}{pen}</div>
                </div>""", unsafe_allow_html=True)

                if show_regenerate and r32_teams and matchup_df is not None and scenario_name:
                    if st.button("🔄", key=f"regen_{mid}",
                                 help=f"Regenerate M{mid} and cascade forward"):
                        new_results = regenerate_from_match(
                            results, mid, r32_teams, matchup_df, scenario_name, strength)
                        st.session_state.current_results  = new_results
                        st.session_state.current_scenario = scenario_name
                        st.session_state.current_strength = strength
                        st.rerun()
        st.divider()

    final = results.get(FINAL_ID)
    third = results.get(THIRD_PLACE_ID)
    if final:
        champion  = final["winner"]
        runner_up = final["team2"] if champion == final["team1"] else final["team1"]
        third_line = ""
        if third:
            tw = third["winner"]; tl = third["team2"] if tw == third["team1"] else third["team1"]
            third_line = (f'<div style="margin-top:0.5rem;font-size:0.8rem;color:#92400e;">'
                          f'🥉 {flag(tw)} {tw} &nbsp;|&nbsp; 4th: {flag(tl)} {tl}</div>')
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1c1400 0%,#2d1f00 100%);
                    border:2px solid #f59e0b;border-radius:16px;padding:2rem;
                    text-align:center;margin-top:1rem;">
            <div style="font-size:0.75rem;letter-spacing:0.3em;color:#b45309;">
                🏆 &nbsp; WORLD CUP 2026 CHAMPION &nbsp; 🏆</div>
            <div style="font-size:3rem;font-weight:bold;color:#f59e0b;margin:0.5rem 0;">
                {flag(champion)} {champion}</div>
            <div style="color:#92400e;font-size:0.85rem;">
                defeated {flag(runner_up)} {runner_up} in the final · {final['score']}</div>
            {third_line}
        </div>""", unsafe_allow_html=True)

# MAIN PAGE

def render_scenarios_page(matchup_df: pd.DataFrame = None, knockout_df: pd.DataFrame = None):
    st.title("🎲 Alternate Realities")

    for key, default in [("current_results", None), ("current_scenario", "Most Likely (Default)"),
                          ("current_strength", 1.0), ("scenario_attempts", {})]:
        if key not in st.session_state:
            st.session_state[key] = default

    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                padding:1.5rem;margin-bottom:1.5rem;">
        <p style="color:#94a3b8;margin:0;font-size:0.9rem;line-height:1.6;">
            🌍 Explore different possible World Cup 2026 timelines.<br>
            • <strong>Most Likely</strong> — same outcome every time, from your 500 simulations<br>
            • <strong>Other scenarios</strong> — random, different every click<br>
            • Adjust <strong>Strength</strong> to control how extreme the effect is<br>
            • Click <strong>🔄</strong> on any match to re-roll it and cascade forward
        </p>
    </div>""", unsafe_allow_html=True)

    if matchup_df is None or knockout_df is None:
        st.error("Data not loaded. Please restart the app.")
        return

    # Build from passed DataFrames — zero CSV reads here
    r32_teams           = load_r32_from_df(knockout_df)
    most_likely_bracket = load_most_likely_from_df(knockout_df)

    scenario_names = list(SCENARIOS.keys())
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        selected_scenario = st.selectbox("Choose a timeline:", scenario_names,
            index=scenario_names.index(st.session_state.current_scenario))
    is_det = SCENARIOS[selected_scenario]["deterministic"]

    with col2:
        strength = st.slider("🎚️ Strength", 0.0, 2.0,
            value=st.session_state.current_strength, step=0.1,
            disabled=is_det, help="0=no effect · 1=normal · 2=extreme")

    with col3:
        if st.button("🎲 SURPRISE ME!", use_container_width=True):
            st.session_state.current_scenario = random.choice(
                [s for s in scenario_names if not SCENARIOS[s]["deterministic"]])
            st.rerun()

    st.info(f"💡 {SCENARIOS[selected_scenario]['description']}")
    if not is_det:
        st.caption(f"🎲 Attempt #{st.session_state.scenario_attempts.get(selected_scenario, 0) + 1}"
                   " — each click gives a different outcome!")

    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        simulate_clicked = st.button(
            "🎲 GENERATE NEW REALITY" if not is_det else "✅ SHOW MOST LIKELY OUTCOME",
            use_container_width=True, type="primary")

    if simulate_clicked:
        if not is_det:
            st.session_state.scenario_attempts[selected_scenario] = \
                st.session_state.scenario_attempts.get(selected_scenario, 0) + 1

        with st.spinner(f"Simulating {selected_scenario}..."):
            results = simulate_full_tournament(
                selected_scenario, r32_teams, matchup_df, strength,
                most_likely_bracket=most_likely_bracket,  # ← always passed
            )

        # Integrity check for random scenarios only
        if not is_det:
            champ = results.get(FINAL_ID, {}).get("winner")
            if champ and champ not in (results.get(101, {}).get("winner"),
                                       results.get(102, {}).get("winner")):
                st.error("⚠️ Bracket error detected. Please click Generate again.")
                st.stop()

        st.session_state.current_results  = results
        st.session_state.current_scenario = selected_scenario
        st.session_state.current_strength = strength
        st.rerun()

    if st.session_state.current_results:
        cur_scenario = st.session_state.current_scenario
        cur_strength = st.session_state.current_strength
        render_complete_bracket(
            st.session_state.current_results, f"🏆 {cur_scenario}",
            show_regenerate=not SCENARIOS[cur_scenario]["deterministic"],
            r32_teams=r32_teams, matchup_df=matchup_df,
            scenario_name=cur_scenario, strength=cur_strength,
        )
        _, save_col, _ = st.columns([1, 2, 1])
        with save_col:
            if st.button("💾 SAVE THIS TIMELINE TO FAVORITES", use_container_width=True):
                fid = save_favorite_bracket(
                    st.session_state.current_results, cur_scenario, cur_strength)
                st.success(f"✅ Saved! ID: {fid}")

    st.markdown("---")
    st.markdown("### ⭐ Saved Timelines")
    favorites = load_favorites()
    if not favorites:
        st.caption("No saved timelines yet.")
    else:
        for fav in reversed(favorites[-10:]):
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(f"**{fav['scenario']}** (strength {fav['strength']}) — "
                            f"Champion: {flag(fav['champion'])} **{fav['champion']}** · {fav['date']}")
            with c2:
                if st.button("Load", key=f"load_{fav['id']}"):
                    st.session_state.current_results  = {int(k): v for k, v in fav["results"].items()}
                    st.session_state.current_scenario = fav["scenario"]
                    st.session_state.current_strength = fav["strength"]
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"del_{fav['id']}"):
                    favs = [f for f in load_favorites() if f["id"] != fav["id"]]
                    _fav_path().write_text(json.dumps(favs, indent=2))
                    st.rerun()


if __name__ == "__main__":
    render_scenarios_page()