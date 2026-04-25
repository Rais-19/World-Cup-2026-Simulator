# frontend/scenarios_page.py
"""
Alternate Realities - Simulate different tournament scenarios using REAL probabilities
With randomization, strength sliders, and save functionality
"""

import streamlit as st
import pandas as pd
import random
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Load data once
@st.cache_data
def load_matchup_data():
    """Load matchup probabilities"""
    data_dir = Path(__file__).parent.parent / "data"
    matchup_df = pd.read_csv(data_dir / "matchup_probabilities.csv")
    return matchup_df

@st.cache_data
def load_bracket_structure():
    """Load knockout bracket structure"""
    data_dir = Path(__file__).parent.parent / "data"
    knockout_df = pd.read_csv(data_dir / "knockout_bracket.csv")
    
    # Build bracket dictionary
    bracket = {}
    for _, row in knockout_df.iterrows():
        match_id = int(row['Match_ID'])
        bracket[match_id] = {
            'round': row['Round'],
            'team1': row['Team1'],
            'team2': row['Team2'],
            'most_likely': row['Most_Likely_Winner'],
            'prob': row['Probability']
        }
    return bracket

# Flag emojis
FLAG_EMOJI = {
    "Argentina": "🇦🇷", "France": "🇫🇷", "Spain": "🇪🇸", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Brazil": "🇧🇷", "Portugal": "🇵🇹", "Belgium": "🇧🇪", "Netherlands": "🇳🇱",
    "Germany": "🇩🇪", "Croatia": "🇭🇷", "Morocco": "🇲🇦", "USA": "🇺🇸",
    "Colombia": "🇨🇴", "Mexico": "🇲🇽", "Japan": "🇯🇵", "Uruguay": "🇺🇾",
    "Senegal": "🇸🇳", "Switzerland": "🇨🇭", "Iran": "🇮🇷", "South Korea": "🇰🇷",
    "Australia": "🇦🇺", "Austria": "🇦🇹", "Ecuador": "🇪🇨", "Turkey": "🇹🇷",
    "Sweden": "🇸🇪", "Norway": "🇳🇴", "Algeria": "🇩🇿", "Egypt": "🇪🇬",
    "Czech Republic": "🇨🇿", "Qatar": "🇶🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Canada": "🇨🇦",
    "Ivory Coast": "🇨🇮", "Tunisia": "🇹🇳", "Paraguay": "🇵🇾", "Saudi Arabia": "🇸🇦",
    "DR Congo": "🇨🇩", "Ghana": "🇬🇭", "Bosnia": "🇧🇦", "South Africa": "🇿🇦",
    "Jordan": "🇯🇴", "Cape Verde": "🇨🇻", "Iraq": "🇮🇶", "Uzbekistan": "🇺🇿",
    "Panama": "🇵🇦", "New Zealand": "🇳🇿", "Haiti": "🇭🇹", "Curacao": "🇨🇼",
}

def flag(team: str) -> str:
    return FLAG_EMOJI.get(team, "🏳️")

def save_favorite_bracket(results: Dict, scenario_name: str, strength: float):
    """Save a favorite bracket outcome to file"""
    data_dir = Path(__file__).parent.parent / "data"
    favorites_file = data_dir / "favorite_brackets.json"
    
    # Load existing favorites
    favorites = []
    if favorites_file.exists():
        with open(favorites_file, 'r') as f:
            favorites = json.load(f)
    
    # Create favorite entry
    favorite = {
        'id': hashlib.md5(f"{datetime.now()}{scenario_name}{strength}".encode()).hexdigest()[:8],
        'scenario': scenario_name,
        'strength': strength,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'champion': results.get(103, {}).get('winner', 'Unknown'),
        'results': {str(k): v for k, v in results.items()}  # Convert keys to strings for JSON
    }
    
    favorites.append(favorite)
    
    # Keep only last 20 favorites
    if len(favorites) > 20:
        favorites = favorites[-20:]
    
    with open(favorites_file, 'w') as f:
        json.dump(favorites, f, indent=2)
    
    return favorite['id']

def load_favorites():
    """Load saved favorite brackets"""
    data_dir = Path(__file__).parent.parent / "data"
    favorites_file = data_dir / "favorite_brackets.json"
    
    if favorites_file.exists():
        with open(favorites_file, 'r') as f:
            return json.load(f)
    return []

def simulate_match(team1: str, team2: str, matchup_df: pd.DataFrame, scenario_modifier: float = 0, strength: float = 1.0) -> Dict:
    """
    Simulate one match using real probabilities from matchup_df
    scenario_modifier: positive = favors underdog, negative = favors favorite
    strength: multiplier for scenario effect (0-2 range, 1 = normal)
    """
    # Find matchup probabilities
    matchup = matchup_df[
        ((matchup_df['Home'] == team1) & (matchup_df['Away'] == team2)) |
        ((matchup_df['Home'] == team2) & (matchup_df['Away'] == team1))
    ]
    
    if len(matchup) > 0:
        match = matchup.iloc[0]
        if match['Home'] == team1:
            home_win = match['Home_Win_Prob']
            away_win = match['Away_Win_Prob']
            draw = match['Draw_Prob']
            expected_home = match['Expected_Home_Goals']
            expected_away = match['Expected_Away_Goals']
        else:
            # Swap if teams are reversed
            home_win = match['Away_Win_Prob']
            away_win = match['Home_Win_Prob']
            draw = match['Draw_Prob']
            expected_home = match['Expected_Away_Goals']
            expected_away = match['Expected_Home_Goals']
    else:
        # Fallback if no matchup data
        home_win, draw, away_win = 45, 20, 35
        expected_home, expected_away = 1.5, 1.3
    
    # Apply scenario modifier with strength multiplier
    if scenario_modifier != 0:
        adjusted_modifier = scenario_modifier * strength
        # Underdog is the team with lower win probability
        if home_win > away_win:
            home_win = max(5, home_win - adjusted_modifier)
            away_win = min(85, away_win + adjusted_modifier)
        else:
            home_win = min(85, home_win + adjusted_modifier)
            away_win = max(5, away_win - adjusted_modifier)
        draw = 100 - home_win - away_win
        # Ensure draw isn't negative
        if draw < 0:
            draw = 0
            # Redistribute to winner/loser proportionally
            total = home_win + away_win
            if total > 0:
                home_win = home_win / total * 100
                away_win = away_win / total * 100
    
    # Simulate result
    r = random.random() * 100
    
    if r < home_win:
        winner = team1
        # Generate score based on expected goals
        goals1 = max(0, int(random.gauss(expected_home, 1.2)))
        goals2 = max(0, int(random.gauss(expected_away, 1.0)))
        # Ensure winner actually wins
        if goals1 <= goals2:
            goals1 = goals2 + random.randint(1, 3)
        is_penalties = False
    elif r < home_win + draw:
        # Draw - will go to penalties in knockout
        goals = max(0, int(random.gauss((expected_home + expected_away)/2, 0.8)))
        goals1, goals2 = goals, goals
        winner = random.choice([team1, team2])  # Penalty shootout
        is_penalties = True
    else:
        winner = team2
        goals2 = max(0, int(random.gauss(expected_away, 1.2)))
        goals1 = max(0, int(random.gauss(expected_home, 1.0)))
        if goals2 <= goals1:
            goals2 = goals1 + random.randint(1, 3)
        is_penalties = False
    
    # Keep scores realistic (max 7 goals)
    goals1 = min(goals1, 7)
    goals2 = min(goals2, 7)
    
    return {
        "team1": team1,
        "team2": team2,
        "score": f"{goals1} - {goals2}",
        "winner": winner,
        "is_penalties": is_penalties
    }

def simulate_full_tournament(scenario_name: str, bracket_structure: Dict, matchup_df: pd.DataFrame, 
                            strength: float = 1.0, random_seed: Optional[int] = None) -> Dict:
    """Simulate complete tournament based on scenario"""
    
    # Set seed for reproducibility if provided
    if random_seed is not None:
        random.seed(random_seed)
    elif scenario_name == "Most Likely (Default)":
        # Deterministic for default scenario
        random.seed(42)
    else:
        # Random for other scenarios - no fixed seed
        random.seed()
    
    # Scenario modifiers (base values before strength multiplier)
    base_modifiers = {
        "Most Likely (Default)": 0,
        "Giant Killers (Upsets)": 18,
        "European Dominance": -12,
        "South American Revival": 12,
        "Home Advantage": 10,
        "Golden Generation": -8
    }
    
    modifier = base_modifiers.get(scenario_name, 0)
    
    results = {}
    winners_by_match = {}
    
    # Get all matches sorted by round
    rounds_order = ["Round of 32", "Round of 16", "Quarter-Final", "Semi-Final", "Final", "Third Place"]
    
    for round_name in rounds_order:
        # Get matches for this round
        round_matches = {mid: data for mid, data in bracket_structure.items() 
                        if data['round'] == round_name}
        
        for match_id, match_data in round_matches.items():
            team1 = match_data['team1']
            team2 = match_data['team2']
            
            # Handle placeholder winners from previous rounds
            if "Winner" in str(team1) or "Match" in str(team1):
                import re
                numbers = re.findall(r'\d+', str(team1))
                if numbers:
                    prev_match = int(numbers[0])
                    if prev_match in results:
                        team1 = results[prev_match]['winner']
            
            if "Winner" in str(team2) or "Match" in str(team2):
                import re
                numbers = re.findall(r'\d+', str(team2))
                if numbers:
                    prev_match = int(numbers[0])
                    if prev_match in results:
                        team2 = results[prev_match]['winner']
            
            # Skip if teams not determined yet
            if team1 and team2 and "TBD" not in team1 and "TBD" not in team2 and team1 != "Unknown" and team2 != "Unknown":
                result = simulate_match(team1, team2, matchup_df, modifier, strength)
                result['match_id'] = match_id
                result['round'] = round_name
                results[match_id] = result
                winners_by_match[match_id] = result['winner']
    
    return results

def regenerate_single_match(results: Dict, match_id: int, bracket_structure: Dict, 
                           matchup_df: pd.DataFrame, scenario_name: str, strength: float) -> Dict:
    """Regenerate a single match and all downstream matches"""
    # Get the match data
    match_data = bracket_structure.get(match_id)
    if not match_data:
        return results
    
    # Simulate just this match
    team1 = match_data['team1']
    team2 = match_data['team2']
    
    # Handle placeholders
    if "Winner" in str(team1) or "Match" in str(team1):
        import re
        numbers = re.findall(r'\d+', str(team1))
        if numbers:
            prev_match = int(numbers[0])
            if prev_match in results:
                team1 = results[prev_match]['winner']
    
    if "Winner" in str(team2) or "Match" in str(team2):
        import re
        numbers = re.findall(r'\d+', str(team2))
        if numbers:
            prev_match = int(numbers[0])
            if prev_match in results:
                team2 = results[prev_match]['winner']
    
    base_modifiers = {
        "Most Likely (Default)": 0,
        "Giant Killers (Upsets)": 18,
        "European Dominance": -12,
        "South American Revival": 12,
        "Home Advantage": 10,
        "Golden Generation": -8
    }
    modifier = base_modifiers.get(scenario_name, 0)
    
    # Simulate new result
    new_result = simulate_match(team1, team2, matchup_df, modifier, strength)
    new_result['match_id'] = match_id
    new_result['round'] = match_data['round']
    results[match_id] = new_result
    
    # Need to re-simulate all downstream matches
    # Find all matches that depend on this one
    downstream_matches = []
    for mid, data in bracket_structure.items():
        if "Winner" in str(data['team1']) or "Match" in str(data['team1']):
            import re
            numbers = re.findall(r'\d+', str(data['team1']))
            if numbers and int(numbers[0]) == match_id:
                downstream_matches.append(mid)
        if "Winner" in str(data['team2']) or "Match" in str(data['team2']):
            import re
            numbers = re.findall(r'\d+', str(data['team2']))
            if numbers and int(numbers[0]) == match_id:
                downstream_matches.append(mid)
    
    # Re-simulate downstream matches in order
    for down_id in sorted(downstream_matches):
        down_data = bracket_structure[down_id]
        t1 = down_data['team1']
        t2 = down_data['team2']
        
        # Resolve placeholders
        if "Winner" in str(t1) or "Match" in str(t1):
            import re
            numbers = re.findall(r'\d+', str(t1))
            if numbers:
                prev_match = int(numbers[0])
                if prev_match in results:
                    t1 = results[prev_match]['winner']
        
        if "Winner" in str(t2) or "Match" in str(t2):
            import re
            numbers = re.findall(r'\d+', str(t2))
            if numbers:
                prev_match = int(numbers[0])
                if prev_match in results:
                    t2 = results[prev_match]['winner']
        
        if t1 and t2 and "TBD" not in t1 and "TBD" not in t2:
            new_down_result = simulate_match(t1, t2, matchup_df, modifier, strength)
            new_down_result['match_id'] = down_id
            new_down_result['round'] = down_data['round']
            results[down_id] = new_down_result
    
    return results

def render_complete_bracket(results: Dict, title: str, show_regenerate: bool = False, 
                           bracket_structure: Dict = None, matchup_df: pd.DataFrame = None,
                           scenario_name: str = None, strength: float = 1.0):
    """Display complete bracket with all scores and optional regenerate buttons"""
    
    st.markdown(f"### {title}")
    
    # Define rounds
    rounds = [
        ("Round of 32", list(range(73, 89)), 4),
        ("Round of 16", list(range(89, 97)), 4),
        ("Quarter-Final", list(range(97, 101)), 2),
        ("Semi-Final", list(range(101, 103)), 2),
        ("Final", [103], 1),
    ]
    
    for round_name, match_ids, num_cols in rounds:
        st.markdown(f"#### {round_name}")
        
        # Get matches that exist in results
        matches = [results[mid] for mid in match_ids if mid in results]
        
        if matches:
            cols = st.columns(min(num_cols, len(matches)))
            for idx, match in enumerate(matches):
                with cols[idx % len(cols)]:
                    # Determine winner styling
                    if match['winner'] == match['team1']:
                        team1_style = "color: #f59e0b; font-weight: bold;"
                        team2_style = "color: #64748b;"
                    else:
                        team1_style = "color: #64748b;"
                        team2_style = "color: #f59e0b; font-weight: bold;"
                    
                    penalty_badge = " (P)" if match.get('is_penalties') else ""
                    
                    st.markdown(f"""
                    <div style="background: #0f172a; border: 1px solid #1e293b; 
                                border-radius: 10px; padding: 0.75rem; margin: 0.5rem 0;">
                        <div style="font-size: 0.7rem; color: #475569;">{round_name}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin: 0.5rem 0;">
                            <span style="{team1_style}">{flag(match['team1'])} {match['team1']}</span>
                            <span style="font-family: monospace; font-weight: bold; color: #f59e0b;">
                                {match['score']}
                            </span>
                            <span style="{team2_style}">{flag(match['team2'])} {match['team2']}</span>
                        </div>
                        <div style="border-top: 1px solid #1e293b; margin: 0.5rem 0;"></div>
                        <div style="font-size: 0.75rem; color: #10b981;">
                            🏆 Winner: {flag(match['winner'])} {match['winner']}{penalty_badge}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add regenerate button for each match if enabled
                    # FIXED: Check if matchup_df is not None and not empty
                    if show_regenerate and bracket_structure and matchup_df is not None and len(matchup_df) > 0 and scenario_name:
                        col_btn1, col_btn2, col_btn3 = st.columns([1,1,1])
                        with col_btn2:
                            if st.button(f"🔄", key=f"reg_match_{match.get('match_id', idx)}", help="Regenerate this match"):
                                new_results = regenerate_single_match(
                                    results.copy(), match.get('match_id'), bracket_structure, 
                                    matchup_df, scenario_name, strength
                                )
                                st.session_state.manual_regenerated = new_results
                                st.rerun()
        
        st.divider()
    
    # Show champion
    final_match = results.get(103)
    if final_match:
        champion = final_match['winner']
        runner_up = final_match['team2'] if champion == final_match['team1'] else final_match['team1']
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1c1400 0%, #2d1f00 100%);
                    border: 2px solid #f59e0b;
                    border-radius: 16px; 
                    padding: 2rem; 
                    text-align: center;
                    margin-top: 1rem;">
            <div style="font-size: 0.8rem; letter-spacing: 0.3em; color: #b45309;">🏆 WORLD CUP 2026 CHAMPION 🏆</div>
            <div style="font-size: 3rem; font-weight: bold; color: #f59e0b; margin: 0.5rem 0;">
                {flag(champion)} {champion}
            </div>
            <div style="color: #92400e; font-size: 0.85rem;">
                Defeated {flag(runner_up)} {runner_up} in the final
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_scenarios_page():
    """Main scenarios page"""
    
    st.title("🎲 Alternate Realities")
    
    # Initialize session state
    if "scenario_attempts" not in st.session_state:
        st.session_state.scenario_attempts = {}
    if "manual_regenerated" not in st.session_state:
        st.session_state.manual_regenerated = None
    
    st.markdown("""
    <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; 
                padding: 1.5rem; margin-bottom: 1.5rem;">
        <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">
            🌍 Explore different possible timelines for World Cup 2026.<br>
            • <strong>Most Likely</strong> = Same outcome every time (based on simulations)<br>
            • <strong>Other scenarios</strong> = Different outcome EACH click!<br>
            • Adjust the <strong>strength slider</strong> to control how extreme the scenario is<br>
            • Click <strong>🔄 on any match</strong> to regenerate just that match and its downstream results!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    matchup_df = load_matchup_data()
    bracket_structure = load_bracket_structure()
    
    # Scenario selector
    scenarios = [
        "Most Likely (Default)",
        "Giant Killers (Upsets)",
        "European Dominance",
        "South American Revival",
        "Home Advantage",
        "Golden Generation"
    ]
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_scenario = st.selectbox(
            "Choose a timeline to explore:",
            scenarios,
            help="Most Likely = deterministic. Others = random each click!"
        )
    
    with col2:
        # Option B: Strength slider
        strength = st.slider(
            "🎚️ Scenario Strength",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="0 = no effect, 1 = normal, 2 = extreme effect",
            disabled=(selected_scenario == "Most Likely (Default)")
        )
    
    with col3:
        # Option A: Surprise Me button
        if st.button("🎲 SURPRISE ME!", use_container_width=True):
            # Randomly select a non-default scenario
            surprise_scenario = random.choice(scenarios[1:])  # Exclude "Most Likely"
            st.session_state.surprise_scenario = surprise_scenario
            st.session_state.force_simulate = True
            st.rerun()
    
    # Handle surprise scenario
    if "surprise_scenario" in st.session_state:
        selected_scenario = st.session_state.surprise_scenario
        st.info(f"🎲 Surprise! You got: **{selected_scenario}**")
    
    # Button text based on scenario
    is_random_scenario = selected_scenario != "Most Likely (Default)"
    button_text = "🎲 GENERATE NEW REALITY" if is_random_scenario else "🎲 GENERATE THIS REALITY"
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        simulate_button = st.button(button_text, use_container_width=True, type="primary")
    
    # Track attempts for random scenarios
    if is_random_scenario and selected_scenario not in st.session_state.scenario_attempts:
        st.session_state.scenario_attempts[selected_scenario] = 0
    
    # Scenario descriptions
    scenario_descriptions = {
        "Most Likely (Default)": "Based purely on team strengths and probabilities. The most probable outcome. Same every time.",
        "Giant Killers (Upsets)": "Underdogs perform better. Expect more upsets and Cinderella stories! Different each click!",
        "European Dominance": "European teams show their strength. Expect a European champion. Different each click!",
        "South American Revival": "South American teams dominate. Brazil/Argentina favorites. Different each click!",
        "Home Advantage": "North American teams get a boost from home support. Different each click!",
        "Golden Generation": "Star players perform at their peak. Favorites usually win. Different each click!"
    }
    
    st.info(f"💡 **Scenario Context:** {scenario_descriptions[selected_scenario]}")
    
    # Show attempt counter for random scenarios
    if is_random_scenario:
        attempt_count = st.session_state.scenario_attempts.get(selected_scenario, 0)
        st.caption(f"🎲 Attempt #{attempt_count + 1} - Each click gives a different outcome!")
    
    # Simulate when button clicked or regeneration occurs
    if simulate_button or "force_simulate" in st.session_state or st.session_state.manual_regenerated:
        
        if simulate_button and is_random_scenario:
            # Increment attempt counter
            st.session_state.scenario_attempts[selected_scenario] = st.session_state.scenario_attempts.get(selected_scenario, 0) + 1
        
        # Get results
        if st.session_state.manual_regenerated:
            results = st.session_state.manual_regenerated
            st.session_state.manual_regenerated = None
        else:
            with st.spinner(f"Simulating {selected_scenario} timeline..."):
                results = simulate_full_tournament(selected_scenario, bracket_structure, matchup_df, strength)
            
            # Auto-save to session for potential favorite saving
            st.session_state.current_results = results
            st.session_state.current_scenario = selected_scenario
            st.session_state.current_strength = strength
        
        # Display the bracket with regenerate buttons
        render_complete_bracket(
            results, 
            f"🏆 {selected_scenario}", 
            show_regenerate=True,
            bracket_structure=bracket_structure,
            matchup_df=matchup_df,
            scenario_name=selected_scenario,
            strength=strength
        )
        
        # Option C: Save favorite button
        col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
        with col_save2:
            if st.button("💾 SAVE THIS TIMELINE TO FAVORITES", use_container_width=True):
                favorite_id = save_favorite_bracket(results, selected_scenario, strength)
                st.success(f"✅ Timeline saved! ID: {favorite_id}")
        
        # Display saved favorites section
        st.markdown("---")
        st.markdown("### ⭐ Saved Timelines")
        
        favorites = load_favorites()
        if favorites:
            # Show last 5 favorites
            for fav in favorites[-5:]:
                col_fav1, col_fav2, col_fav3 = st.columns([3, 1, 1])
                with col_fav1:
                    st.markdown(f"**{fav['scenario']}** (Strength: {fav['strength']}) - Champion: {flag(fav['champion'])} {fav['champion']}")
                    st.caption(f"Saved: {fav['date']}")
                with col_fav2:
                    if st.button(f"Load", key=f"load_{fav['id']}"):
                        # Convert results back from JSON
                        loaded_results = {int(k): v for k, v in fav['results'].items()}
                        st.session_state.current_results = loaded_results
                        st.session_state.manual_regenerated = loaded_results
                        st.rerun()
                with col_fav3:
                    if st.button(f"🗑️", key=f"del_{fav['id']}"):
                        # Remove from favorites
                        favorites.remove(fav)
                        with open(Path(__file__).parent.parent / "data" / "favorite_brackets.json", 'w') as f:
                            json.dump(favorites, f, indent=2)
                        st.rerun()
        else:
            st.caption("No saved timelines yet. Click 'Save Timeline' above to save your favorites!")
        
        # Clear force_simulate flag
        if "force_simulate" in st.session_state:
            del st.session_state.force_simulate
        if "surprise_scenario" in st.session_state:
            del st.session_state.surprise_scenario
    
    elif "current_results" in st.session_state:
        # Show previously generated results
        render_complete_bracket(
            st.session_state.current_results, 
            f"🏆 {st.session_state.current_scenario}", 
            show_regenerate=True,
            bracket_structure=bracket_structure,
            matchup_df=matchup_df,
            scenario_name=st.session_state.current_scenario,
            strength=st.session_state.current_strength
        )

# For testing
if __name__ == "__main__":
    render_scenarios_page()