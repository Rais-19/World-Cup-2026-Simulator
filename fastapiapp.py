from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path

# Import services
from services.results_service import results_service
from services.prediction_service import prediction_service
from services.bracket_service import bracket_service

app = FastAPI(
    title="WC 2026 Simulation API",
    description="World Cup 2026 Monte Carlo Simulation Results",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HEALTH CHECK

@app.get("/")
def root():
    return {
        "message": "WC 2026 Simulation API",
        "status": "running",
        "total_simulations": results_service.get_statistics().get("total_simulations", 5000)
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# CHAMPION PROBABILITIES

@app.get("/api/champion-probabilities")
def get_champion_probabilities(limit: int = 10):
    """Get top N champion probabilities"""
    return results_service.get_champion_ranking(top_n=limit)

@app.get("/api/champion-probability/{team}")
def get_team_champion_probability(team: str):
    """Get champion probability for a specific team"""
    prob = results_service.get_team_champion_prob(team)
    if prob == 0:
        raise HTTPException(status_code=404, detail=f"Team '{team}' not found")
    return {"team": team, "champion_probability": prob}

# GROUP STAGE

@app.get("/api/groups")
def get_all_groups():
    """Get all groups with teams"""
    return bracket_service.groups

@app.get("/api/groups/{group_name}")
def get_group_standings(group_name: str):
    """Get standings for a specific group"""
    standings = results_service.get_group_table(group_name)
    if not standings:
        raise HTTPException(status_code=404, detail=f"Group '{group_name}' not found")
    return {"group": group_name, "standings": standings}

@app.get("/api/all-group-standings")
def get_all_group_standings():
    """Get all group standings"""
    return results_service.get_all_groups()

# TEAM STRENGTH

@app.get("/api/team-strength")
def get_team_strength(limit: int = 48):
    """Get team strength ranking by Elo"""
    strength = results_service.get_team_strength()
    return strength[:limit]

@app.get("/api/team-strength/{team}")
def get_team_strength_by_name(team: str):
    """Get Elo and ranking for a specific team"""
    team_data = results_service.get_team_strength_by_name(team)
    if not team_data:
        raise HTTPException(status_code=404, detail=f"Team '{team}' not found")
    return team_data

# KNOCKOUT BRACKET

@app.get("/api/knockout-bracket")
def get_knockout_bracket():
    """Get most likely knockout bracket"""
    return results_service.get_knockout_bracket()

@app.get("/api/round/{round_name}")
def get_round_matches(round_name: str):
    """Get matches for a specific round (Round of 32, Round of 16, Quarter-Final, Semi-Final, Final)"""
    matches = results_service.get_round_matches(round_name)
    if not matches:
        raise HTTPException(status_code=404, detail=f"Round '{round_name}' not found")
    return {"round": round_name, "matches": matches}

# STAGE SURVIVAL

@app.get("/api/stage-survival/{team}")
def get_team_survival(team: str):
    """Get probability team reaches each stage"""
    survival = results_service.get_team_stage_survival(team)
    if not survival:
        raise HTTPException(status_code=404, detail=f"Team '{team}' not found")
    return {"team": team, "survival_probabilities": survival}

@app.get("/api/stage-survival")
def get_all_survival():
    """Get stage survival for all teams"""
    return results_service.get_all_survival()

# MATCHUP PREDICTIONS

@app.post("/api/predict")
def predict_match(home: str, away: str, use_precomputed: bool = True):
    """
    Predict match outcome between two teams.
    use_precomputed=True: Load from saved CSV 
    use_precomputed=False: Run ML model (slower but available for any matchup)
    """
    if use_precomputed:
        # Try to load from pre-computed results
        result = results_service.get_matchup_probability(home, away)
        if result:
            return result
    
    # Fallback to ML model
    return prediction_service.predict_match(home, away)

@app.get("/api/upset-probability/{favorite}/{underdog}")
def get_upset_probability(favorite: str, underdog: str):
    """Get upset probability for a matchup"""
    prob = results_service.get_upset_probability(favorite, underdog)
    return {
        "favorite": favorite,
        "underdog": underdog,
        "upset_probability": prob,
        "favorite_wins_probability": 100 - prob if prob else None
    }

# TOURNAMENT STATISTICS

@app.get("/api/statistics")
def get_simulation_statistics():
    """Get overall simulation statistics"""
    return results_service.get_statistics()

@app.get("/api/confederation-performance")
def get_confederation_performance():
    """Get performance by confederation"""
    return results_service.get_confederation_performance()

@app.get("/api/top-upsets")
def get_top_upsets(limit: int = 10):
    """Get biggest upset potentials"""
    upsets = results_service.get_upset_probabilities()
    return upsets[:limit]

# TEAM LIST

@app.get("/api/teams")
def get_all_teams():
    """Get list of all 48 teams"""
    return prediction_service.get_all_teams()

@app.get("/api/teams/search/{query}")
def search_teams(query: str):
    """Search teams by name"""
    all_teams = prediction_service.get_all_teams()
    results = [t for t in all_teams if query.lower() in t.lower()]
    return {"query": query, "results": results[:10]}

# RUN SERVER 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)