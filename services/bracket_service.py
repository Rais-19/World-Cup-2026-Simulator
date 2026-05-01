import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from config.tournament_config import (
    ROUND_OF_16_PAIRINGS,
    QUARTER_FINAL_PAIRINGS,
    SEMI_FINAL_PAIRINGS,
    THIRD_PLACE_MATCH,
    FINAL_MATCH,
    BRACKET_ROUNDS,
    FIFA_2026_RANK,
)
from services.data_store import get_knockout_bracket, get_matchup_probabilities

#  Data paths
_HERE = Path(__file__).parent.parent
DATA_DIR = _HERE / "data"

_BRACKET_CSV   = DATA_DIR / "knockout_bracket.csv"
_MATCHUP_CSV   = DATA_DIR / "matchup_probabilities.csv"
_GROUP_CSV     = DATA_DIR / "group_stage_summary.csv"
_CHAMPION_CSV  = DATA_DIR / "champion_probabilities.csv"


# DATA LOADING

def load_bracket_data() -> Dict[int, Dict]:
    """
    Load knockout_bracket.csv and return a dict keyed by match_id.

    """
    if not _BRACKET_CSV.exists():
        return {}
    df = get_knockout_bracket()

    # Normalise column names defensively
    df.columns = [c.strip() for c in df.columns]

    bracket = {}
    for _, row in df.iterrows():
        mid = int(row["Match_ID"])
        winner = str(row.get("Most_Likely_Winner", "")).strip()
        team1  = str(row.get("Team1", "")).strip()
        team2  = str(row.get("Team2", "")).strip()

        # Integrity check: winner must be one of the two teams
        if winner not in (team1, team2):
            winner = team1  # safe fallback

        bracket[mid] = {
            "round":               str(row.get("Round", "")),
            "team1":               team1,
            "team2":               team2,
            "most_likely_winner":  winner,
            "probability":         float(row.get("Probability", 50.0)),
        }

    return bracket


def load_matchup_data() -> pd.DataFrame:
    """
    Load matchup_probabilities.csv.
    Returns empty DataFrame if file missing.
    """
    if not _MATCHUP_CSV.exists():
        return pd.DataFrame()
    return get_matchup_probabilities()


def load_group_data() -> pd.DataFrame:
    """Load group_stage_summary.csv."""
    if not _GROUP_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(_GROUP_CSV)


def load_champion_data() -> pd.DataFrame:
    """Load champion_probabilities.csv."""
    if not _CHAMPION_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(_CHAMPION_CSV)


# HEAD-TO-HEAD LOOKUP

def get_matchup_probs(
    home: str,
    away: str,
    matchup_df: Optional[pd.DataFrame] = None,
) -> Optional[Dict[str, float]]:
    """
    Look up head-to-head probabilities for home vs away.

    Tries (home, away) first; if not found tries (away, home) and
    swaps the probabilities so the result always reflects the
    requested home/away orientation.

    Returns None if neither direction is in the CSV.
    """
    if matchup_df is None:
        matchup_df = load_matchup_data()

    if matchup_df.empty:
        return None

    # Primary lookup
    row = matchup_df[(matchup_df["Home"] == home) & (matchup_df["Away"] == away)]
    if not row.empty:
        r = row.iloc[0]
        return {
            "home_win":   float(r["Home_Win_Prob"]),
            "draw":       float(r["Draw_Prob"]),
            "away_win":   float(r["Away_Win_Prob"]),
            "home_goals": float(r["Expected_Home_Goals"]),
            "away_goals": float(r["Expected_Away_Goals"]),
        }

    # Reverse lookup — swap everything
    row = matchup_df[(matchup_df["Home"] == away) & (matchup_df["Away"] == home)]
    if not row.empty:
        r = row.iloc[0]
        return {
            "home_win":   float(r["Away_Win_Prob"]),
            "draw":       float(r["Draw_Prob"]),
            "away_win":   float(r["Home_Win_Prob"]),
            "home_goals": float(r["Expected_Away_Goals"]),
            "away_goals": float(r["Expected_Home_Goals"]),
        }

    return None


# BRACKET STRUCTURE BUILDER

def build_r32_bracket(
    winners: Dict[str, str],
    runners_up: Dict[str, str],
    best_8_thirds: List[str],
) -> Dict[int, Tuple[str, str]]:
    """
    Build Round-of-32 matchups from qualified teams.

    Parameters
    ----------
    winners      : {'A': 'Mexico', 'B': 'Canada', ...}
    runners_up   : {'A': 'South Korea', 'B': 'Switzerland', ...}
    best_8_thirds: ordered list of 8 best third-place teams

    Returns
    -------
    {73: ('Mexico', 'Switzerland'), 74: ('Germany', 'ThirdTeam'), ...}
    """
    thirds = list(best_8_thirds) + [None] * 8 

    bracket = {
        # Winners vs Runners-up 
        73: (winners.get("A"),    runners_up.get("B")),   # 1A vs 2B
        75: (winners.get("F"),    runners_up.get("C")),   # 1F vs 2C
        76: (winners.get("C"),    runners_up.get("F")),   # 1C vs 2F
        78: (runners_up.get("E"), runners_up.get("I")),   # 2E vs 2I
        83: (runners_up.get("K"), runners_up.get("L")),   # 2K vs 2L
        84: (winners.get("H"),    runners_up.get("J")),   # 1H vs 2J
        86: (winners.get("J"),    runners_up.get("H")),   # 1J vs 2H
        88: (runners_up.get("D"), runners_up.get("G")),   # 2D vs 2G

        #  Winners vs Third-place 
        74: (winners.get("E"),  thirds[0]),   # 1E vs 3ABCDEF
        77: (winners.get("I"),  thirds[1]),   # 1I vs 3CDEFGH
        79: (runners_up.get("A"), thirds[2]), # 2A vs 3CEFHI  ← FIXED
        80: (winners.get("L"),  thirds[3]),   # 1L vs 3EHIJKL
        81: (winners.get("D"),  thirds[4]),   # 1D vs 3BEFIJ
        82: (winners.get("G"),  thirds[5]),   # 1G vs 3AEHIJ
        85: (winners.get("B"),  thirds[6]),   # 1B vs 3EFGIJ
        87: (winners.get("K"),  thirds[7]),   # 1K vs 3DEIJKL
    }

    # Drop any match where a team resolved to None
    return {mid: (t1, t2) for mid, (t1, t2) in bracket.items() if t1 and t2}


# CASCADE LOGIC  (Manual override mode)

def cascade_bracket(
    r32_picks: Dict[int, str],
    matchup_df: Optional[pd.DataFrame] = None,
) -> Dict[int, Dict]:
    """
    Given user-selected winners for R32 matches, cascade them through
    R16 → QF → SF → Final and return a full bracket state dict.

    Parameters
    ----------
    r32_picks : {match_id: winning_team}  — user selections for M73-M88.
                Matches not yet picked have no entry (or value = None).

    Returns
    -------
    {
      match_id: {
        'team1': str | None,
        'team2': str | None,
        'winner': str | None,       # None = not yet decided
        'probability': float | None # from CSV if available
      }
    }
    """
    if matchup_df is None:
        matchup_df = load_matchup_data()

    state: Dict[int, Dict] = {}

    # Seed R32 results
    for mid, winner in r32_picks.items():
        state[mid] = {"winner": winner}

    def get_winner(mid: int) -> Optional[str]:
        return state.get(mid, {}).get("winner")

    def resolve_match(match_id: int, src1: int, src2: int) -> None:
        t1 = get_winner(src1)
        t2 = get_winner(src2)
        probs = get_matchup_probs(t1, t2, matchup_df) if (t1 and t2) else None
        state[match_id] = {
            "team1":       t1,
            "team2":       t2,
            "winner":      None,    # user hasn't picked yet
            "home_win":    probs["home_win"]  if probs else None,
            "draw":        probs["draw"]      if probs else None,
            "away_win":    probs["away_win"]  if probs else None,
            "home_goals":  probs["home_goals"]if probs else None,
            "away_goals":  probs["away_goals"]if probs else None,
        }

    # R16 — fed by R32
    for r16_id, (m1, m2) in ROUND_OF_16_PAIRINGS.items():
        resolve_match(r16_id, m1, m2)

    # Carry over any R16 picks the user has already made
    # (caller may pass {92: 'Germany', ...} mixed in with r32_picks)
    for mid, winner in r32_picks.items():
        if mid in ROUND_OF_16_PAIRINGS:
            state[mid]["winner"] = winner

    # QF — fed by R16
    for qf_id, (m1, m2) in QUARTER_FINAL_PAIRINGS.items():
        resolve_match(qf_id, m1, m2)

    for mid, winner in r32_picks.items():
        if mid in QUARTER_FINAL_PAIRINGS:
            state[mid]["winner"] = winner

    # SF — fed by QF
    for sf_id, (m1, m2) in SEMI_FINAL_PAIRINGS.items():
        resolve_match(sf_id, m1, m2)

    for mid, winner in r32_picks.items():
        if mid in SEMI_FINAL_PAIRINGS:
            state[mid]["winner"] = winner

    # Final — fed by SF
    resolve_match(FINAL_MATCH, 101, 102)

    if FINAL_MATCH in r32_picks:
        state[FINAL_MATCH]["winner"] = r32_picks[FINAL_MATCH]

    return state


# AI AUTO-SIMULATION (single run)

def _pick_winner(
    team1: str,
    team2: str,
    matchup_df: pd.DataFrame,
) -> Tuple[str, Optional[Dict]]:
    """
    Pick winner probabilistically from matchup data.
    Falls back to Elo-based coin flip if no data available.
    """
    probs = get_matchup_probs(team1, team2, matchup_df)

    if probs:
        hw = probs["home_win"] / 100
        aw = probs["away_win"] / 100
        total = hw + aw
        if total > 0:
            hw_norm = hw / total
        else:
            hw_norm = 0.5
        winner = team1 if random.random() < hw_norm else team2
    else:
        # Elo fallback
        r1 = FIFA_2026_RANK.get(team1, 80)
        r2 = FIFA_2026_RANK.get(team2, 80)
        p1 = 1 / (1 + 10 ** ((r1 - r2) / 20))
        winner = team1 if random.random() < p1 else team2

    return winner, probs


def simulate_full_bracket(
    winners: Dict[str, str],
    runners_up: Dict[str, str],
    best_8_thirds: List[str],
    matchup_df: Optional[pd.DataFrame] = None,
) -> Dict[int, Dict]:
    """
    Run one complete AI simulation of the knockout bracket.

    Returns full match_results dict keyed by match_id, each entry:
    {
      'round': str, 'team1': str, 'team2': str,
      'winner': str, 'loser': str,
      'home_win': float, 'draw': float, 'away_win': float,
      'home_goals': float, 'away_goals': float
    }
    """
    if matchup_df is None:
        matchup_df = load_matchup_data()

    r32 = build_r32_bracket(winners, runners_up, best_8_thirds)
    match_results: Dict[int, Dict] = {}
    match_winners: Dict[int, str]  = {}

    def play(match_id: int, t1: str, t2: str, round_name: str) -> str:
        winner, probs = _pick_winner(t1, t2, matchup_df)
        loser = t2 if winner == t1 else t1
        match_results[match_id] = {
            "round":      round_name,
            "team1":      t1,
            "team2":      t2,
            "winner":     winner,
            "loser":      loser,
            "home_win":   probs["home_win"]   if probs else None,
            "draw":       probs["draw"]       if probs else None,
            "away_win":   probs["away_win"]   if probs else None,
            "home_goals": probs["home_goals"] if probs else None,
            "away_goals": probs["away_goals"] if probs else None,
        }
        match_winners[match_id] = winner
        return winner

    # R32
    for mid in sorted(r32):
        t1, t2 = r32[mid]
        play(mid, t1, t2, "Round of 32")

    # R16
    for r16_id, (m1, m2) in ROUND_OF_16_PAIRINGS.items():
        t1 = match_winners.get(m1)
        t2 = match_winners.get(m2)
        if t1 and t2:
            play(r16_id, t1, t2, "Round of 16")

    # QF
    for qf_id, (m1, m2) in QUARTER_FINAL_PAIRINGS.items():
        t1 = match_winners.get(m1)
        t2 = match_winners.get(m2)
        if t1 and t2:
            play(qf_id, t1, t2, "Quarter-Final")

    # SF
    sf_losers = []
    for sf_id, (m1, m2) in SEMI_FINAL_PAIRINGS.items():
        t1 = match_winners.get(m1)
        t2 = match_winners.get(m2)
        if t1 and t2:
            winner = play(sf_id, t1, t2, "Semi-Final")
            sf_losers.append(t2 if winner == t1 else t1)

    # Third place
    if len(sf_losers) == 2:
        play(THIRD_PLACE_MATCH, sf_losers[0], sf_losers[1], "Third Place")

    # Final
    t1 = match_winners.get(101)
    t2 = match_winners.get(102)
    if t1 and t2:
        play(FINAL_MATCH, t1, t2, "Final")

    return match_results


# BRACKET STATE HELPERS (used by frontend)

def get_bracket_teams_by_round(
    bracket_data: Dict[int, Dict],
) -> Dict[str, List[Dict]]:
    """
    Group bracket match data by round name for easy rendering.

    Returns
    -------
    {
      'Round of 32': [{'match_id': 73, 'team1': ..., ...}, ...],
      'Round of 16': [...],
      ...
    }
    """
    result: Dict[str, List] = {r: [] for r in BRACKET_ROUNDS}

    for mid, data in bracket_data.items():
        round_name = data.get("round", "")
        if round_name in result:
            result[round_name].append({"match_id": mid, **data})

    # Sort each round by match_id
    for round_name in result:
        result[round_name].sort(key=lambda x: x["match_id"])

    return result


def get_champion_from_bracket(bracket_data: Dict[int, Dict]) -> Optional[str]:
    """Return the champion from a completed bracket, or None."""
    final = bracket_data.get(FINAL_MATCH)
    if final:
        return final.get("winner") or final.get("most_likely_winner")
    return None


def validate_bracket_integrity(bracket_data: Dict[int, Dict]) -> Tuple[bool, List[str]]:
    """
    Check that no team appears as winner in more than one match
    per round. Returns (is_valid, list_of_errors).
    """
    errors = []
    round_winners: Dict[str, set] = {}

    for mid, data in bracket_data.items():
        round_name = data.get("round", "")
        winner = data.get("winner") or data.get("most_likely_winner")
        team1  = data.get("team1", "")
        team2  = data.get("team2", "")

        if not winner:
            continue

        # Winner must be one of the two teams
        if winner not in (team1, team2):
            errors.append(
                f"M{mid}: winner '{winner}' is not in ({team1}, {team2})"
            )

        # No duplicate winners per round
        if round_name not in round_winners:
            round_winners[round_name] = set()
        if winner in round_winners[round_name]:
            errors.append(f"M{mid}: '{winner}' wins twice in {round_name}")
        round_winners[round_name].add(winner)

    return (len(errors) == 0), errors



# SINGLETON

class BracketService:
    """
    Thin wrapper that exposes all bracket functions as methods,
    caches loaded data, and provides a clean API for the frontend.
    """

    def __init__(self):
        self._bracket_data:  Optional[Dict]          = None
        self._matchup_df:    Optional[pd.DataFrame]  = None
        self._group_df:      Optional[pd.DataFrame]  = None
        self._champion_df:   Optional[pd.DataFrame]  = None

    # Cached loaders 

    @property
    def bracket_data(self) -> Dict[int, Dict]:
        if self._bracket_data is None:
            self._bracket_data = load_bracket_data()
        return self._bracket_data

    @property
    def matchup_df(self) -> pd.DataFrame:
        if self._matchup_df is None:
            self._matchup_df = load_matchup_data()
        return self._matchup_df

    @property
    def group_df(self) -> pd.DataFrame:
        if self._group_df is None:
            self._group_df = load_group_data()
        return self._group_df

    @property
    def champion_df(self) -> pd.DataFrame:
        if self._champion_df is None:
            self._champion_df = load_champion_data()
        return self._champion_df

    # Public API

    def get_matchup(self, home: str, away: str) -> Optional[Dict]:
        return get_matchup_probs(home, away, self.matchup_df)

    def cascade(self, picks: Dict[int, str]) -> Dict[int, Dict]:
        return cascade_bracket(picks, self.matchup_df)

    def simulate(
        self,
        winners: Dict[str, str],
        runners_up: Dict[str, str],
        best_8_thirds: List[str],
    ) -> Dict[int, Dict]:
        return simulate_full_bracket(winners, runners_up, best_8_thirds, self.matchup_df)

    def ai_bracket_by_round(self) -> Dict[str, List[Dict]]:
        return get_bracket_teams_by_round(self.bracket_data)

    def validate(self) -> Tuple[bool, List[str]]:
        return validate_bracket_integrity(self.bracket_data)

    def champion(self) -> Optional[str]:
        return get_champion_from_bracket(self.bracket_data)

    def reload(self) -> None:
        """Force reload all cached data."""
        self._bracket_data = None
        self._matchup_df   = None
        self._group_df     = None
        self._champion_df  = None


bracket_service = BracketService()
