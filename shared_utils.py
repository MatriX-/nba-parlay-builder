"""
Shared Utilities for NBA Parlay Builder
Consolidates common functions used across multiple modules
"""
import pandas as pd
import numpy as np

# ============================================================
# PLAYER POSITION NORMALIZATION
# ============================================================

NORMALIZED_POS = {
    "PG": "PG", "G": "PG",
    "SG": "SG",
    "SF": "SF",
    "PF": "PF", "F": "PF",
    "C": "C",
}

# This will be populated at runtime
POSITION_MAP = {}


def populate_position_map(season: str = "2024-25"):
    """
    Populate POSITION_MAP from NBA API roster data.
    Call this at app startup to ensure positions are available.
    """
    global POSITION_MAP
    from nba_api.stats.static import teams as teams_static
    from nba_api.stats.endpoints import commonteamroster
    
    try:
        all_teams = teams_static.get_teams()
        for team in all_teams:
            team_id = team["id"]
            try:
                roster = commonteamroster.CommonTeamRoster(
                    team_id=team_id,
                    season=season
                ).get_data_frames()[0]
                
                if "PLAYER_ID" in roster.columns and "POSITION" in roster.columns:
                    for _, row in roster.iterrows():
                        pid = row["PLAYER_ID"]
                        pos = row["POSITION"]
                        # Normalize position
                        POSITION_MAP[pid] = NORMALIZED_POS.get(pos, pos)
            except Exception:
                continue  # Skip teams with roster fetch errors
    except Exception as e:
        print(f"Warning: Could not populate position map: {e}")


def get_player_position(pid):
    """Get player position, fallback to SG if unknown"""
    pos = POSITION_MAP.get(pid)
    if not pos:
        return "SG"  # fallback assumption
    return NORMALIZED_POS.get(pos, "SG")


# ============================================================
# TEXT FORMATTING UTILITIES
# ============================================================

def ordinal(n: int) -> str:
    """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def player_prefix(name: str, stat: str) -> str:
    """
    Build player name prefix like: MITCHELL PRA
    Handles Jr./Sr. etc.
    """
    STAT_PREFIX_LABEL = {
        "PTS": "PTS",
        "REB": "REB",
        "AST": "AST",
        "PRA": "PRA",
        "FG3M": "3PM",
    }
    
    tokens = name.split()
    if len(tokens) == 1:
        last_name = tokens[0]
    else:
        suffixes = {"Jr.", "Jr", "Sr.", "Sr", "II", "III", "IV"}
        if tokens[-1] in suffixes:
            last_name = tokens[-2] + " " + tokens[-1]
        else:
            last_name = tokens[-1]
    label = STAT_PREFIX_LABEL.get(stat, stat)
    return f"{last_name.upper()} {label.upper()}"


# ============================================================
# STATISTICAL UTILITIES
# ============================================================

def logistic_prob(z: float) -> float:
    """
    Map z-score to probability (0.05 to 0.95 range)
    Keeps values in a reasonable, not-too-confident range.
    """
    p = 0.5 + 0.18 * z
    return float(np.clip(p, 0.05, 0.95))


def to_minutes(val) -> float:
    """
    Convert MM:SS string to minutes as float
    Returns float for better precision in calculations
    """
    if pd.isna(val) or val == '' or val is None:
        return 0.0
    s = str(val)
    if ':' in s:
        parts = s.split(':')
        return float(parts[0]) + float(parts[1]) / 60.0
    try:
        return float(s)
    except:
        return 0.0


# ============================================================
# IMAGE UTILITIES
# ============================================================

def get_player_headshot(player_id: int) -> str:
    """
    Get player headshot URL
    Using 1040x760 for best quality
    """
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"


# ============================================================
# TEAM ABBREVIATION MAPPING
# ============================================================

# ESPN uses 2-letter codes, NBA API uses 3-letter codes
ABBREV_MAP = {
    "GS": "GSW",
    "NO": "NOP",
    "UT": "UTA",
    "SA": "SAS",
    "LA": "LAL",
    "NY": "NYK",
    "WSH": "WAS",
    # Pass-throughs for already-canonical codes
    "GSW": "GSW",
    "NOP": "NOP",
    "UTA": "UTA",
    "SAS": "SAS",
    "LAL": "LAL",
    "NYK": "NYK",
    "WAS": "WAS",
}


def normalize_team_abbrev(abbrev: str) -> str:
    """Normalize team abbreviation to 3-letter NBA format"""
    return ABBREV_MAP.get(abbrev, abbrev)
