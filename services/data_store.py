from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def get_matchup_probabilities() -> pd.DataFrame:
    """Load matchup data once per process with memory-friendly dtypes."""
    df = pd.read_csv(
        DATA_DIR / "matchup_probabilities.csv",
        usecols=[
            "Home",
            "Away",
            "Home_Win_Prob",
            "Draw_Prob",
            "Away_Win_Prob",
            "Expected_Home_Goals",
            "Expected_Away_Goals",
        ],
    )
    float_cols = [
        "Home_Win_Prob",
        "Draw_Prob",
        "Away_Win_Prob",
        "Expected_Home_Goals",
        "Expected_Away_Goals",
    ]
    df[float_cols] = df[float_cols].astype("float32")
    return df


@lru_cache(maxsize=1)
def get_knockout_bracket() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "knockout_bracket.csv")


def find_matchup_row(home: str, away: str) -> Optional[pd.Series]:
    """Return a row for home/away, handling reversed fixtures."""
    matchup_df = get_matchup_probabilities()
    row = matchup_df[(matchup_df["Home"] == home) & (matchup_df["Away"] == away)]
    if not row.empty:
        return row.iloc[0]

    row = matchup_df[(matchup_df["Home"] == away) & (matchup_df["Away"] == home)]
    if not row.empty:
        return row.iloc[0]

    return None
