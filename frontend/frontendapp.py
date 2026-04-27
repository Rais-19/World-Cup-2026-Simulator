import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

# Page config 
st.set_page_config(
    page_title="WC 2026 Tournament Simulator",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Data loading
@st.cache_data
def load_data():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    try:
        with open(data_dir / "simulation_metadata.json", "r") as f:
            master_data = json.load(f)
    except Exception:
        champion_df = pd.read_csv(data_dir / "champion_probabilities.csv")
        master_data = {"metadata": {
            "total_simulations": 500,
            "most_likely_champion": champion_df.iloc[0]["Team"],
        }}
    return {
        "champion":       pd.read_csv(data_dir / "champion_probabilities.csv"),
        "group":          pd.read_csv(data_dir / "group_stage_summary.csv"),
        "team_strength":  pd.read_csv(data_dir / "team_strength.csv"),
        "knockout":       pd.read_csv(data_dir / "knockout_bracket.csv"),
        "stage_survival": pd.read_csv(data_dir / "stage_survival.csv"),
        "upset":          pd.read_csv(data_dir / "upset_probabilities.csv"),
        "matchup":        pd.read_csv(data_dir / "matchup_probabilities.csv"),
        "metadata":       master_data.get("metadata", {}),
    }

data = load_data()

# Sidebar
st.sidebar.title("🏆 WC 2026 Simulator")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    [
        "🏆 Champion Probabilities",
        "📊 Group Stage",
        "🥅 Knockout Bracket",
        "🔍 Matchup Predictor",
        "🎲 Alternate Realities",
        "🏟️ Interactive Bracket",
        "📈 Team Stats",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    f"""
    **Simulation Stats:**
    - {data['metadata'].get('total_simulations', '500')} simulations
    - 48 teams | 12 groups
    - Most likely: {data['metadata'].get('most_likely_champion', 'Spain')}
    """
)

# PAGE 1: CHAMPION PROBABILITIES
if page == "🏆 Champion Probabilities":
    st.title("🏆 World Cup 2026 Champion Probabilities")
    st.markdown(f"Based on **{data['metadata'].get('total_simulations', '5000')}** Monte Carlo simulations")

    col1, col2 = st.columns([2, 1])
    with col1:
        top15 = data["champion"].head(15)
        fig = px.bar(
            top15, x="Probability", y="Team", orientation="h",
            title="Top 15 Most Likely Champions", text="Probability",
            color="Probability", color_continuous_scale="Viridis", height=500,
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🏅 Top Contenders")
        for i, (_, row) in enumerate(data["champion"].head(3).iterrows()):
            bc = "#FFD700" if i == 0 else "#C0C0C0" if i == 1 else "#CD7F32"
            tc = "#FFD700" if i == 0 else "#ffffff"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                        padding:15px;border-radius:10px;margin-bottom:10px;
                        border-left:5px solid {bc}">
                <h3 style="margin:0">{i+1}. {row['Team']}</h3>
                <p style="font-size:24px;margin:0;color:{tc}">{row['Probability']:.1f}%</p>
            </div>""", unsafe_allow_html=True)

    with st.expander("📋 Full Championship Probabilities"):
        st.dataframe(
            data["champion"].style.format({"Probability": "{:.1f}%"}),
            use_container_width=True, height=400,
        )


# PAGE 2: GROUP STAGE
elif page == "📊 Group Stage":
    st.title("📊 Group Stage Analysis")

    groups = sorted(data["group"]["Group"].unique())
    selected_group = st.selectbox("Select Group", groups)
    group_data = data["group"][data["group"]["Group"] == selected_group].copy()
    group_data = group_data.sort_values("1st_Place_Prob", ascending=False)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"Group {selected_group.replace('Group ', '')} Standings")
        display_df = group_data[
            ["Team","1st_Place_Prob","2nd_Place_Prob","3rd_Place_Prob","4th_Place_Prob","Advance_Prob"]
        ].copy()
        display_df.columns = ["Team","1st %","2nd %","3rd %","4th %","Advance %"]

        def highlight_advance(row):
            if row["Advance %"] > 50:  return ["background-color:#2e7d32"] * len(row)
            if row["Advance %"] > 20:  return ["background-color:#f9a825"] * len(row)
            return [""] * len(row)

        st.dataframe(
            display_df.style
                .format({c: "{:.1f}%" for c in display_df.columns if "%" in c})
                .apply(highlight_advance, axis=1),
            use_container_width=True,
        )

    with col2:
        fig = go.Figure()
        for pos, color in [
            ("1st_Place_Prob","#FFD700"), ("2nd_Place_Prob","#C0C0C0"),
            ("3rd_Place_Prob","#CD7F32"), ("4th_Place_Prob","#8B4513"),
        ]:
            fig.add_trace(go.Bar(
                name=pos.replace("_Place_Prob",""),
                x=group_data["Team"], y=group_data[pos],
                marker_color=color, text=group_data[pos].round(1), textposition="inside",
            ))
        fig.update_layout(title="Position Probabilities", barmode="stack",
                          height=400, yaxis_title="Probability (%)")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💀 Group of Death Analysis")
    gc = (data["group"].groupby("Group")
          .agg({"Advance_Prob":"std","1st_Place_Prob":"max"})
          .reset_index().sort_values("Advance_Prob"))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Most Competitive Groups**")
        for _, r in gc.head(3).iterrows():
            st.write(f"• {r['Group']}: {r['Advance_Prob']:.1f}% balance score")
    with col2:
        st.markdown("**Most Predictable Groups**")
        for _, r in gc.tail(3).iterrows():
            st.write(f"• {r['Group']}: {r['Advance_Prob']:.1f}% balance score")

# PAGE 3: KNOCKOUT BRACKET
elif page == "🥅 Knockout Bracket":
    st.title("🥅 Knockout Bracket — Most Likely Path")

    rounds = data["knockout"]["Round"].unique()
    selected_round = st.selectbox("Select Round", rounds)
    round_data = data["knockout"][data["knockout"]["Round"] == selected_round]

    st.subheader(f"📋 {selected_round} Matches")
    cols = st.columns(2)
    for i, (_, match) in enumerate(round_data.iterrows()):
        with cols[i % 2]:
            w = match["Most_Likely_Winner"]
            t1, t2 = match["Team1"], match["Team2"]
            t1s = "font-weight:bold;color:#4CAF50;" if w == t1 else ""
            t2s = "font-weight:bold;color:#4CAF50;" if w == t2 else ""
            st.markdown(f"""
            <div style="background:#1e1e2e;padding:12px;border-radius:8px;
                        margin:8px 0;border-left:3px solid #4CAF50;">
                <p style="font-size:10px;color:#888;margin:0;">Match {int(match['Match_ID'])}</p>
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin:8px 0;">
                    <span style="font-size:14px;{t1s}">{t1}</span>
                    <span style="color:#666;font-size:12px;">VS</span>
                    <span style="font-size:14px;{t2s}">{t2}</span>
                </div>
                <div style="border-top:1px solid #333;margin:5px 0;"></div>
                <p style="font-size:12px;margin:5px 0;color:#4CAF50;">
                    🏆 <strong>{w}</strong> wins ({match['Probability']:.1f}%)
                </p>
            </div>""", unsafe_allow_html=True)

    with st.expander("📊 View All Matches as Table"):
        df = round_data[["Match_ID","Team1","Team2","Most_Likely_Winner","Probability"]].copy()
        df.columns = ["Match","Team 1","Team 2","Winner","Win %"]
        st.dataframe(df, use_container_width=True, height=400)

    # Complete bracket tree
    st.subheader("🏆 Complete Bracket Tree")
    lines = ["\n"+"="*60, "WC 2026 MOST LIKELY BRACKET", "="*60+"\n"]
    for rnd in ["Round of 32","Round of 16","Quarter-Final","Semi-Final","Final"]:
        rd = data["knockout"][data["knockout"]["Round"] == rnd]
        if len(rd):
            lines += [f"\n{'─'*50}", f"🔹 {rnd.upper()}", f"{'─'*50}"]
            for _, m in rd.iterrows():
                lines.append(
                    f"   Match {int(m['Match_ID'])}: {m['Team1']} vs "
                    f"{m['Team2']} → {m['Most_Likely_Winner']} ({m['Probability']:.1f}%)"
                )
    st.code("\n".join(lines), language="text")

    final_m = data["knockout"][data["knockout"]["Round"] == "Final"]
    if len(final_m):
        f = final_m.iloc[0]
        champ = f["Most_Likely_Winner"]
        opp   = f["Team2"] if champ == f["Team1"] else f["Team1"]
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#FFD700,#FFA500);
                    padding:25px;border-radius:15px;text-align:center;">
            <h2 style="color:#1a1a2e;margin:0;">🏆 PREDICTED CHAMPION 🏆</h2>
            <h1 style="color:#1a1a2e;font-size:42px;">{champ}</h1>
            <p style="color:#1a1a2e;">defeated {opp} in the final</p>
        </div>""", unsafe_allow_html=True)

# PAGE 4: MATCHUP PREDICTOR
elif page == "🔍 Matchup Predictor":
    st.title("🔍 Matchup Predictor")
    st.markdown("Select any two teams to see head-to-head probabilities")

    all_teams = sorted(data["team_strength"]["Team"].unique())
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("Home Team", all_teams,
            index=all_teams.index("Spain") if "Spain" in all_teams else 0)
    with col2:
        away_team = st.selectbox("Away Team", all_teams,
            index=all_teams.index("Argentina") if "Argentina" in all_teams else 1)

    if home_team == away_team:
        st.warning("Please select two different teams")
    else:
        m = data["matchup"][
            ((data["matchup"]["Home"] == home_team) & (data["matchup"]["Away"] == away_team)) |
            ((data["matchup"]["Home"] == away_team) & (data["matchup"]["Away"] == home_team))
        ]
        if len(m):
            r = m.iloc[0]
            if r["Home"] == home_team:
                hp, ap = r["Home_Win_Prob"], r["Away_Win_Prob"]
            else:
                hp, ap = r["Away_Win_Prob"], r["Home_Win_Prob"]
            dp = r["Draw_Prob"]
            col1, col2, col3 = st.columns(3)
            with col1: st.metric(f"🏠 {home_team}", f"{hp:.1f}%")
            with col2: st.metric("🤝 Draw", f"{dp:.1f}%")
            with col3: st.metric(f"✈️ {away_team}", f"{ap:.1f}%")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[home_team,"Draw",away_team], y=[hp,dp,ap],
                marker_color=["#2e7d32","#f9a825","#c62828"],
                text=[f"{hp:.1f}%",f"{dp:.1f}%",f"{ap:.1f}%"],
                textposition="auto",
            ))
            fig.update_layout(title="Match Outcome Probabilities",
                              yaxis_title="Probability (%)", height=400)
            st.plotly_chart(fig, use_container_width=True)
            if min(hp, ap) > 40:
                lower = away_team if hp > ap else home_team
                st.warning(f"⚠️ Close matchup! {lower} has a {min(hp,ap):.1f}% chance to win.")
        else:
            st.error("Matchup data not found. Try another combination.")

# PAGE 5: ALTERNATE REALITIES 
elif page == "🎲 Alternate Realities":
    from scenarios_page import render_scenarios_page
    render_scenarios_page()

# PAGE 6: INTERACTIVE BRACKET
elif page == "🏟️ Interactive Bracket":
    from bracket_page import render_bracket_page
    render_bracket_page()

# PAGE 7: TEAM STATS
elif page == "📈 Team Stats":
    st.title("📈 Team Strength & Statistics")

    all_teams = sorted(data["team_strength"]["Team"].unique())
    selected_team = st.selectbox("Select Team", all_teams)
    td = data["team_strength"][data["team_strength"]["Team"] == selected_team].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Elo Rating", f"{td['Elo']:.0f}")
    with col2: st.metric("FIFA Rank", f"#{int(td['FIFA_Rank'])}")
    with col3:
        cp = data["champion"][data["champion"]["Team"] == selected_team]["Probability"].values
        st.metric("Champion Probability", f"{cp[0]:.1f}%" if len(cp) else "0%")
    with col4: st.metric("Best Stage", td.get("Best_Stage", "Group Stage"))

    st.subheader(f"{selected_team} — Tournament Progression")
    sd = data["stage_survival"][data["stage_survival"]["Team"] == selected_team]
    if len(sd):
        stages = ["Group Stage","Round of 32","Round of 16",
                  "Quarter-Final","Semi-Final","Finalist","Champion"]
        vals = [sd[s].iloc[0] for s in stages if s in sd.columns]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=stages[:len(vals)], y=vals, mode="lines+markers",
            line=dict(color="#FFD700", width=3),
            marker=dict(size=10, color="#FFA500"),
            fill="tozeroy", fillcolor="rgba(255,215,0,0.2)",
        ))
        fig.update_layout(title=f"{selected_team} — Stage Survival",
                          yaxis_title="Probability (%)", height=400)
        st.plotly_chart(fig, use_container_width=True)

    if "Confederation" in data["group"].columns:
        conf = td.get("Confederation", "Unknown")
        cd = data["group"][data["group"]["Confederation"] == conf]
        st.info(f"📊 {conf} avg advance: {cd['Advance_Prob'].mean():.1f}%")

# Footer 
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#666;'>"
    "🏆 WC 2026 Simulation | Monte Carlo | FIFA rankings + Elo ratings"
    "</p>",
    unsafe_allow_html=True,
)