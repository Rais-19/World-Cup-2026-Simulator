import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional

class ResultsService:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.load_all_results()
    
    def load_all_results(self):
        """Load all pre-computed results from Colab"""
        self.champion_probs = pd.read_csv(self.data_dir / "champion_probabilities.csv")
        self.group_summary = pd.read_csv(self.data_dir / "group_stage_summary.csv")
        self.team_strength = pd.read_csv(self.data_dir / "team_strength.csv")
        self.knockout_bracket = pd.read_csv(self.data_dir / "knockout_bracket.csv")
        self.stage_survival = pd.read_csv(self.data_dir / "stage_survival.csv")
        self.upset_probs = pd.read_csv(self.data_dir / "upset_probabilities.csv")
        self.matchup_probs = pd.read_csv(self.data_dir / "matchup_probabilities.csv")
        
        with open(self.data_dir / "master_dashboard_data.json", 'r') as f:
            self.master_data = json.load(f)
    
    def get_champion_ranking(self, top_n: int = 10) -> List[Dict]:
        """Get top N champion probabilities"""
        return self.champion_probs.head(top_n).to_dict('records')
    
    def get_team_champion_prob(self, team: str) -> float:
        """Get champion probability for a specific team"""
        row = self.champion_probs[self.champion_probs['Team'] == team]
        return float(row['Probability'].iloc[0]) if len(row) > 0 else 0.0
    
    def get_group_table(self, group_name: str) -> List[Dict]:
        """Get standings for a specific group"""
        result = self.group_summary[self.group_summary['Group'] == group_name]
        return result.to_dict('records')
    
    def get_all_groups(self) -> Dict[str, List[Dict]]:
        """Get all group standings"""
        groups = {}
        for group in self.group_summary['Group'].unique():
            groups[group] = self.get_group_table(group)
        return groups
    
    def get_team_strength(self) -> List[Dict]:
        """Get team strength ranking by Elo"""
        return self.team_strength.to_dict('records')
    
    def get_team_strength_by_name(self, team: str) -> Optional[Dict]:
        """Get team strength for specific team"""
        row = self.team_strength[self.team_strength['Team'] == team]
        return row.to_dict('records')[0] if len(row) > 0 else None
    
    def get_knockout_bracket(self) -> List[Dict]:
        """Get most likely knockout bracket"""
        return self.knockout_bracket.to_dict('records')
    
    def get_round_matches(self, round_name: str) -> List[Dict]:
        """Get matches for a specific round"""
        matches = self.knockout_bracket[self.knockout_bracket['Round'] == round_name]
        return matches.to_dict('records')
    
    def get_team_stage_survival(self, team: str) -> Optional[Dict]:
        """Get stage survival probabilities for a team"""
        row = self.stage_survival[self.stage_survival['Team'] == team]
        if len(row) > 0:
            return row.iloc[0].to_dict()
        return None
    
    def get_all_survival(self) -> List[Dict]:
        """Get stage survival for all teams"""
        return self.stage_survival.to_dict('records')
    
    def get_matchup_probability(self, home: str, away: str) -> Optional[Dict]:
        """Get pre-computed matchup probability"""
        match = self.matchup_probs[
            (self.matchup_probs['Home'] == home) & 
            (self.matchup_probs['Away'] == away)
        ]
        if len(match) > 0:
            return match.iloc[0].to_dict()
        
        # Check reverse order
        match = self.matchup_probs[
            (self.matchup_probs['Home'] == away) & 
            (self.matchup_probs['Away'] == home)
        ]
        if len(match) > 0:
            row = match.iloc[0].to_dict()
            # Swap home/away
            return {
                'home_team': home,
                'away_team': away,
                'home_win_prob': row['Away_Win_Prob'],
                'draw_prob': row['Draw_Prob'],
                'away_win_prob': row['Home_Win_Prob']
            }
        return None
    
    def get_upset_probability(self, favorite: str, underdog: str) -> float:
        """Get upset probability"""
        upset = self.upset_probs[
            (self.upset_probs['Favorite'] == favorite) & 
            (self.upset_probs['Underdog'] == underdog)
        ]
        return float(upset['Upset_Prob'].iloc[0]) if len(upset) > 0 else 0.0
    
    def get_upset_probabilities(self) -> List[Dict]:
        """Get all upset probabilities sorted"""
        return self.upset_probs.to_dict('records')
    
    def get_confederation_performance(self) -> Dict:
        """Get performance by confederation"""
        perf = self.group_summary.groupby('Confederation').agg({
            'Advance_Prob': 'mean',
            '1st_Place_Prob': 'mean'
        }).round(1).to_dict()
        return perf
    
    def get_statistics(self) -> Dict:
        """Get overall simulation statistics"""
        return self.master_data.get('metadata', {})

# Global instance
results_service = ResultsService()