import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

from config.tournament_config import ALL_TEAMS, FIFA_2026_RANK


class PredictionService:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.models_dir = self.base_dir / "models"
        
        self.match_model = None
        self.home_goals_model = None
        self.away_goals_model = None
        self.goals_scaler = None
        self.feature_cols = None
        self.goals_feature_cols = None
        self.final_elos: Dict[str, float] = {}
        self.match_cache: Dict[Tuple[str, str], Dict] = {}
        
        self.load_models()

    def load_models(self):
        """Load all models safely"""
        print("Loading prediction models...")
        
        try:
            self.match_model = joblib.load(self.models_dir / "match_model.pkl")
            self.home_goals_model = joblib.load(self.models_dir / "home_goals_model.pkl")
            self.away_goals_model = joblib.load(self.models_dir / "away_goals_model.pkl")
            self.goals_scaler = joblib.load(self.models_dir / "goals_scaler.pkl")
            self.feature_cols = joblib.load(self.models_dir / "feature_cols.pkl")
            self.goals_feature_cols = joblib.load(self.models_dir / "goals_features.pkl")
            self.final_elos = joblib.load(self.models_dir / "elo_ratings.pkl")
            
            cache_path = self.models_dir / "match_cache.pkl"
            if cache_path.exists():
                self.match_cache = joblib.load(cache_path)
                print(f"   Match cache loaded: {len(self.match_cache)} matchups")
            
            print(f" Models loaded successfully!")
            print(f"   Match model features: {len(self.feature_cols)}")
            print(f"   Goals model features: {len(self.goals_feature_cols)}")
            print(f"   Elo ratings: {len(self.final_elos)} teams")
            
        except Exception as e:
            print(f" Error loading models: {e}")
            raise

    def get_team_elo(self, team: str) -> float:
        return self.final_elos.get(team, 1500.0)

    def _rank_to_points(self, rank: int) -> float:
        """Convert FIFA rank to points"""
        return max(200.0, 1800.0 - (rank - 1) * 14.5)

    def _elo_to_normalized(self, elo: float, min_elo: float = 1400, max_elo: float = 1800) -> float:
        return max(0.0, min(1.0, (elo - min_elo) / (max_elo - min_elo)))

    def _rank_to_normalized(self, rank: int, max_rank: int = 120) -> float:
        return 1.0 - (rank - 1) / max_rank

    def _compute_pedigree_score(self, team: str) -> float:
        WC_PEDIGREE = {
            'Brazil': (5, 7, 11), 'Germany': (4, 8, 13), 'Italy': (4, 6, 8),
            'Argentina': (3, 5, 7), 'France': (2, 3, 6), 'Uruguay': (2, 2, 5),
            'England': (1, 1, 2), 'Spain': (1, 1, 2), 'Netherlands': (0, 3, 5),
            'Croatia': (0, 1, 3), 'Portugal': (0, 0, 3), 'Belgium': (0, 0, 2),
        }
        data = WC_PEDIGREE.get(team, (0, 0, 0))
        titles, finals, semis = data
        raw = titles * 3 + finals * 1.5 + semis * 0.5
        return min(1.0, raw / 18.0)

    def extract_match_features(self, home_team: str, away_team: str) -> pd.DataFrame:
        """Create features for match outcome model"""
        home_elo = self.get_team_elo(home_team)
        away_elo = self.get_team_elo(away_team)
        home_rank = FIFA_2026_RANK.get(home_team, 80)
        away_rank = FIFA_2026_RANK.get(away_team, 80)
        
        home_strength = 0.55 * self._elo_to_normalized(home_elo) + 0.45 * self._rank_to_normalized(home_rank)
        away_strength = 0.55 * self._elo_to_normalized(away_elo) + 0.45 * self._rank_to_normalized(away_rank)
        home_pedigree = self._compute_pedigree_score(home_team)
        away_pedigree = self._compute_pedigree_score(away_team)
        
        features = {
            'elo_diff': home_elo - away_elo,
            'home_elo': home_elo,
            'away_elo': away_elo,
            'rank_diff': home_rank - away_rank,
            'points_diff': self._rank_to_points(home_rank) - self._rank_to_points(away_rank),
            'strength_diff': home_strength - away_strength,
            'home_strength': home_strength,
            'away_strength': away_strength,
            'home_wc_pedigree': home_pedigree,
            'away_wc_pedigree': away_pedigree,
            'pedigree_diff': home_pedigree - away_pedigree,
            'home_win_rate_last_5': 0.5,
            'away_win_rate_last_5': 0.5,
            'home_gs_avg_last_5': 1.4,
            'away_gs_avg_last_5': 1.2,
            'home_gc_avg_last_5': 1.1,
            'away_gc_avg_last_5': 1.3,
            'home_clean_sheet_rate_last_5': 0.3,
            'away_clean_sheet_rate_last_5': 0.25,
            'neutral': 1,
            'is_penalty_shootout': 0,
            'match_importance': 1.0,
        }
        
        # Override with cache if available
        cache_key = (home_team, away_team)
        if cache_key in self.match_cache:
            cached = self.match_cache[cache_key]
            for key in ['home_win_rate_last_5', 'away_win_rate_last_5', 
                        'home_gs_avg_last_5', 'away_gs_avg_last_5',
                        'home_gc_avg_last_5', 'away_gc_avg_last_5',
                        'home_clean_sheet_rate_last_5', 'away_clean_sheet_rate_last_5']:
                if key in cached:
                    features[key] = cached[key]
        
        df = pd.DataFrame([features])
        if self.feature_cols:
            df = df.reindex(columns=self.feature_cols, fill_value=0)
        
        return df

    def extract_goals_features(self, home_team: str, away_team: str) -> pd.DataFrame:
        """Create features for goals models"""
        home_elo = self.get_team_elo(home_team)
        away_elo = self.get_team_elo(away_team)
        home_rank = FIFA_2026_RANK.get(home_team, 80)
        away_rank = FIFA_2026_RANK.get(away_team, 80)
        
        features = {
            'home_elo': home_elo,
            'away_elo': away_elo,
            'elo_diff': home_elo - away_elo,
            'home_rank': home_rank,
            'away_rank': away_rank,
            'rank_diff': home_rank - away_rank,
            'home_points': self._rank_to_points(home_rank),
            'away_points': self._rank_to_points(away_rank),
            'points_diff': self._rank_to_points(home_rank) - self._rank_to_points(away_rank),
            'home_gs_avg_last_5': 1.4,
            'away_gs_avg_last_5': 1.2,
            'home_gc_avg_last_5': 1.1,
            'away_gc_avg_last_5': 1.3,
            'neutral': 1,
            'match_importance': 1.0,
        }
        
        # Add pedigree if goals model expects it
        if self.goals_feature_cols and 'home_wc_pedigree' in self.goals_feature_cols:
            features['home_wc_pedigree'] = self._compute_pedigree_score(home_team)
            features['away_wc_pedigree'] = self._compute_pedigree_score(away_team)
            features['pedigree_diff'] = self._compute_pedigree_score(home_team) - self._compute_pedigree_score(away_team)
        
        df = pd.DataFrame([features])
        if self.goals_feature_cols:
            df = df.reindex(columns=self.goals_feature_cols, fill_value=0)
        
        return df

    def predict_match(self, home_team: str, away_team: str) -> Dict:
        """Predict match outcome using trained models"""
        cache_key = (home_team, away_team)
        
        # Check cache first
        if cache_key in self.match_cache:
            cached = self.match_cache[cache_key]
            return {
                "home_team": home_team,
                "away_team": away_team,
                "home_win_prob": round(cached['hw_prob'] * 100, 1),
                "draw_prob": round(cached['draw_prob'] * 100, 1),
                "away_win_prob": round(cached['aw_prob'] * 100, 1),
                "expected_goals_home": round(cached['lambda_home'], 2),
                "expected_goals_away": round(cached['lambda_away'], 2),
                "most_likely_score": f"{round(cached['lambda_home'])}–{round(cached['lambda_away'])}"
            }
        
        try:
            X_match = self.extract_match_features(home_team, away_team)
            X_goals = self.extract_goals_features(home_team, away_team)
            
            outcome_probs = self.match_model.predict_proba(X_match)[0]
            
            X_goals_scaled = self.goals_scaler.transform(X_goals)
            home_xg = float(self.home_goals_model.predict(X_goals_scaled)[0])
            away_xg = float(self.away_goals_model.predict(X_goals_scaled)[0])
            home_xg = max(0.15, min(5.0, home_xg))
            away_xg = max(0.15, min(5.0, away_xg))

            return {
                "home_team": home_team,
                "away_team": away_team,
                "home_win_prob": round(float(outcome_probs[0]) * 100, 1),
                "draw_prob": round(float(outcome_probs[1]) * 100, 1),
                "away_win_prob": round(float(outcome_probs[2]) * 100, 1),
                "expected_goals_home": round(home_xg, 2),
                "expected_goals_away": round(away_xg, 2),
                "most_likely_score": f"{round(home_xg)}–{round(away_xg)}"
            }

        except Exception as e:
            print(f"Prediction error {home_team} vs {away_team}: {e}")
            return {
                "home_team": home_team,
                "away_team": away_team,
                "home_win_prob": 48.0,
                "draw_prob": 26.0,
                "away_win_prob": 26.0,
                "expected_goals_home": 1.5,
                "expected_goals_away": 1.2,
                "most_likely_score": "1–1"
            }

    def get_all_teams(self):
        return sorted(ALL_TEAMS)


# Global instance
prediction_service = PredictionService()