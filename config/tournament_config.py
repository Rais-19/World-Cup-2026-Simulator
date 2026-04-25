from typing import Dict, List, Tuple, Optional

# WC 2026 GROUPS (Official Draw)

groups: Dict[str, List[str]] = {
    "Group A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "Group B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "Group C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "Group D": ["United States", "Paraguay", "Australia", "Turkey"],
    "Group E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "Group F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "Group G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "Group H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "Group I": ["France", "Senegal", "Iraq", "Norway"],
    "Group J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "Group K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "Group L": ["England", "Croatia", "Ghana", "Panama"],
}

# ============================================
# FIFA RANKING (For WC 2026 - Anchor Data)
# ============================================

FIFA_2026_RANK: Dict[str, int] = {
    "Argentina": 1, "France": 2, "Spain": 3, "England": 4,
    "Brazil": 5, "Portugal": 6, "Belgium": 7, "Netherlands": 8,
    "Germany": 9, "Croatia": 10, "Italy": 11, "Morocco": 12,
    "United States": 13, "Colombia": 14, "Mexico": 15, "Japan": 16,
    "Uruguay": 17, "Senegal": 18, "Switzerland": 19, "Iran": 21,
    "South Korea": 22, "Australia": 23, "Austria": 24, "Ecuador": 25,
    "Turkey": 28, "Sweden": 29, "Norway": 30, "Algeria": 35,
    "Egypt": 36, "Czech Republic": 36, "Qatar": 37, "Scotland": 38,
    "Canada": 40, "Ivory Coast": 42, "Tunisia": 45, "Paraguay": 55,
    "Saudi Arabia": 56, "DR Congo": 58, "Ghana": 60,
    "Bosnia and Herzegovina": 62, "South Africa": 65, "Jordan": 68,
    "Cape Verde": 70, "Iraq": 75, "Uzbekistan": 80, "Panama": 85,
    "New Zealand": 90, "Haiti": 95, "Curaçao": 100,
}

# ============================================
# ALL PARTICIPATING TEAMS (48 Teams)
# ============================================

ALL_TEAMS: List[str] = [
    "Mexico", "South Africa", "South Korea", "Czech Republic",
    "Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland",
    "Brazil", "Morocco", "Haiti", "Scotland",
    "United States", "Paraguay", "Australia", "Turkey",
    "Germany", "Curaçao", "Ivory Coast", "Ecuador",
    "Netherlands", "Japan", "Sweden", "Tunisia",
    "Belgium", "Egypt", "Iran", "New Zealand",
    "Spain", "Cape Verde", "Saudi Arabia", "Uruguay",
    "France", "Senegal", "Iraq", "Norway",
    "Argentina", "Algeria", "Austria", "Jordan",
    "Portugal", "DR Congo", "Uzbekistan", "Colombia",
    "England", "Croatia", "Ghana", "Panama",
]

# ============================================
# CONFEDERATION MAPPING
# ============================================

CONFEDERATION: Dict[str, str] = {
    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Colombia": "CONMEBOL",
    "Ecuador": "CONMEBOL", "Paraguay": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Spain": "UEFA", "France": "UEFA", "Germany": "UEFA", "England": "UEFA",
    "Netherlands": "UEFA", "Portugal": "UEFA", "Belgium": "UEFA",
    "Croatia": "UEFA", "Switzerland": "UEFA", "Austria": "UEFA",
    "Turkey": "UEFA", "Sweden": "UEFA", "Norway": "UEFA", "Scotland": "UEFA",
    "Czech Republic": "UEFA", "Bosnia and Herzegovina": "UEFA", "Italy": "UEFA",
    "Morocco": "CAF", "Senegal": "CAF", "Egypt": "CAF", "Algeria": "CAF",
    "Ivory Coast": "CAF", "Tunisia": "CAF", "South Africa": "CAF",
    "Cape Verde": "CAF", "DR Congo": "CAF", "Ghana": "CAF",
    "Japan": "AFC", "South Korea": "AFC", "Iran": "AFC", "Australia": "AFC",
    "Saudi Arabia": "AFC", "Qatar": "AFC", "Iraq": "AFC",
    "Uzbekistan": "AFC", "Jordan": "AFC",
    "Mexico": "CONCACAF", "United States": "CONCACAF", "Canada": "CONCACAF",
    "Curaçao": "CONCACAF", "Haiti": "CONCACAF", "Panama": "CONCACAF",
    "New Zealand": "OFC",
}

CONFEDERATION_COLORS: Dict[str, str] = {
    "UEFA":     "#3B82F6",
    "CONMEBOL": "#10B981",
    "CAF":      "#F59E0B",
    "AFC":      "#EF4444",
    "CONCACAF": "#8B5CF6",
    "OFC":      "#EC4899",
}

# ============================================
# BRACKET STRUCTURE (FIXED)
# R32 matchups — each slot appears exactly once
# ============================================

# String notation: '1A' = Winner Group A, '2A' = Runner-up Group A
ROUND_OF_32_MATCHUPS: List[Tuple[str, str]] = [
    ('1A', '2B'),        # Match 73
    ('1E', '3ABCDEF'),   # Match 74
    ('1F', '2C'),        # Match 75
    ('1C', '2F'),        # Match 76
    ('1I', '3CDEFGH'),   # Match 77
    ('2E', '2I'),        # Match 78
    ('2A', '3CEFHI'),    # Match 79 
    ('1L', '3EHIJKL'),   # Match 80
    ('1D', '3BEFIJ'),    # Match 81
    ('1G', '3AEHIJ'),    # Match 82
    ('2K', '2L'),        # Match 83
    ('1H', '2J'),        # Match 84
    ('1B', '3EFGIJ'),    # Match 85
    ('1J', '2H'),        # Match 86
    ('1K', '3DEIJKL'),   # Match 87
    ('2D', '2G'),        # Match 88
]

# Third-place pool definitions
THIRD_PLACE_POOLS: Dict[str, List[str]] = {
    '3ABCDEF': ['A', 'B', 'C', 'D', 'E', 'F'],
    '3CDEFGH': ['C', 'D', 'E', 'F', 'G', 'H'],
    '3CEFHI':  ['C', 'E', 'F', 'H', 'I'],
    '3EHIJKL': ['E', 'H', 'I', 'J', 'K', 'L'],
    '3BEFIJ':  ['B', 'E', 'F', 'I', 'J'],
    '3AEHIJ':  ['A', 'E', 'H', 'I', 'J'],
    '3EFGIJ':  ['E', 'F', 'G', 'I', 'J'],
    '3DEIJKL': ['D', 'E', 'I', 'J', 'K', 'L'],
}

# Ordered mapping of third-place pool → index in best_8_thirds list
THIRD_PLACE_INDEX: Dict[str, int] = {
    '3ABCDEF': 0,
    '3CDEFGH': 1,
    '3CEFHI':  2,
    '3EHIJKL': 3,
    '3BEFIJ':  4,
    '3AEHIJ':  5,
    '3EFGIJ':  6,
    '3DEIJKL': 7,
}

# ============================================
# KNOCKOUT ROUND PAIRINGS
# ============================================

# R16: which two R32 match IDs feed each R16 match
ROUND_OF_16_PAIRINGS: Dict[int, Tuple[int, int]] = {
    89: (74, 77),
    90: (73, 75),
    91: (76, 78),
    92: (79, 80),
    93: (83, 84),
    94: (81, 82),
    95: (86, 88),
    96: (85, 87),
}

# QF: which two R16 match IDs feed each QF
QUARTER_FINAL_PAIRINGS: Dict[int, Tuple[int, int]] = {
    97:  (89, 90),
    98:  (93, 94),
    99:  (91, 92),
    100: (95, 96),
}

# SF: which two QF match IDs feed each SF
SEMI_FINAL_PAIRINGS: Dict[int, Tuple[int, int]] = {
    101: (97, 98),
    102: (99, 100),
}

THIRD_PLACE_MATCH = 104   # losers of 101 and 102
FINAL_MATCH       = 103   # winners of 101 and 102

# Match ID ranges per round
BRACKET_ROUNDS: Dict[str, List[int]] = {
    "Round of 32":   list(range(73, 89)),
    "Round of 16":   list(range(89, 97)),
    "Quarter-Final": list(range(97, 101)),
    "Semi-Final":    list(range(101, 103)),
    "Third Place":   [104],
    "Final":         [103],
}

# Round display order for bracket rendering
ROUND_ORDER = [
    "Round of 32",
    "Round of 16",
    "Quarter-Final",
    "Semi-Final",
    "Final",
]

# ============================================
# TOURNAMENT STAGES
# ============================================

TOURNAMENT_STAGES: Dict[str, Dict] = {
    'group_stage':  {'name': 'Group Stage',       'importance_weight': 0.8,  'has_extra_time': False, 'has_penalties': False},
    'round_of_32':  {'name': 'Round of 32',       'importance_weight': 1.0,  'has_extra_time': True,  'has_penalties': True},
    'round_of_16':  {'name': 'Round of 16',       'importance_weight': 1.2,  'has_extra_time': True,  'has_penalties': True},
    'quarter_final':{'name': 'Quarter-Final',     'importance_weight': 1.4,  'has_extra_time': True,  'has_penalties': True},
    'semi_final':   {'name': 'Semi-Final',        'importance_weight': 1.6,  'has_extra_time': True,  'has_penalties': True},
    'third_place':  {'name': 'Third Place Match', 'importance_weight': 0.9,  'has_extra_time': False, 'has_penalties': True},
    'final':        {'name': 'Final',             'importance_weight': 2.0,  'has_extra_time': True,  'has_penalties': True},
}

# ============================================
# CONSTANTS
# ============================================

NUM_TEAMS         = 48
NUM_GROUPS        = 12
TEAMS_PER_GROUP   = 4
TOTAL_SIMULATIONS = 500

LATE_TOURNAMENT_LIST: List[str] = [
    'FIFA World Cup', 'UEFA Euro', 'Copa América',
    'African Cup of Nations', 'AFC Asian Cup',
    'CONCACAF Gold Cup', 'OFC Nations Cup',
]

TOP_FAVORITES: List[Tuple[str, float]] = [
    ("Spain",       16.0),
    ("France",      13.0),
    ("Argentina",   10.8),
    ("Netherlands",  8.2),
    ("England",      6.6),
    ("Colombia",     6.0),
    ("Brazil",       5.4),
    ("Germany",      5.2),
]

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_team_group(team: str) -> str:
    for group_name, teams in groups.items():
        if team in teams:
            return group_name
    return "Unknown"

def get_group_letter(team: str) -> str:
    for group_name, teams in groups.items():
        if team in teams:
            return group_name.replace("Group ", "")
    return "Unknown"

def get_all_teams_sorted() -> List[str]:
    return sorted(ALL_TEAMS)

def get_team_rank(team: str) -> int:
    return FIFA_2026_RANK.get(team, 100)

def get_team_confederation(team: str) -> str:
    return CONFEDERATION.get(team, "Unknown")

def get_group_teams(group_letter: str) -> List[str]:
    if not group_letter.startswith("Group"):
        group_letter = f"Group {group_letter}"
    return groups.get(group_letter, [])

def rank_to_points(rank: int) -> float:
    return max(200.0, 1800.0 - (rank - 1) * 14.5)

def elo_to_normalized(elo: float, min_elo: float = 1400, max_elo: float = 1800) -> float:
    return max(0.0, min(1.0, (elo - min_elo) / (max_elo - min_elo)))

def rank_to_normalized(rank: int, max_rank: int = 120) -> float:
    return 1.0 - (rank - 1) / max_rank

def get_round_name(match_id: int) -> str:
    for round_name, match_ids in BRACKET_ROUNDS.items():
        if match_id in match_ids:
            return round_name
    return "Unknown"

if __name__ == "__main__":
    print("=" * 60)
    print("WC 2026 CONFIGURATION LOADED")
    print("=" * 60)
    print(f"Total Teams: {NUM_TEAMS} | Groups: {NUM_GROUPS}")
    print()

    # Validate bracket — no duplicate slots
    from collections import Counter
    slots = []
    for notation, _ in ROUND_OF_32_MATCHUPS:
        slots.append(notation)
    for _, notation in ROUND_OF_32_MATCHUPS:
        slots.append(notation)
    winner_slots   = [s for s in slots if s.startswith('1')]
    runner_slots   = [s for s in slots if s.startswith('2')]
    third_slots    = [s for s in slots if s.startswith('3')]
    dup_w = [s for s, c in Counter(winner_slots).items() if c > 1]
    dup_r = [s for s, c in Counter(runner_slots).items() if c > 1]
    if dup_w or dup_r:
        print(f"  ✗ BRACKET BUG — duplicate winner slots: {dup_w}, runner slots: {dup_r}")
    else:
        print(f"  ✓ Bracket structure valid — {len(winner_slots)} winner slots, "
              f"{len(runner_slots)} runner-up slots, {len(third_slots)} third-place slots")