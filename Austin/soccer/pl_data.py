"""
Premier League data fetcher
Uses the official PL API (no key required).
"""

import requests
import pandas as pd

_HEADERS = {
    "Origin": "https://www.premierleague.com",
    "Referer": "https://www.premierleague.com/",
    "User-Agent": "Mozilla/5.0",
}
_BASE = "https://footballapi.pulselive.com/football"

# Stat types → friendly label
STAT_TYPES = {
    "goals":              "Goals",
    "goal_assist":        "Assists",
    "appearances":        "Apps",
    "mins_played":        "Minutes",
    "total_scoring_att":  "Shots",
    "total_pass":         "Passes",
    "total_tackle":       "Tackles",
    "won_tackle":         "Tackles Won",
    "interception":       "Interceptions",
    "total_clearance":    "Clearances",
    "total_aerial_won":   "Aerials Won",
    "total_cross":        "Crosses",
    "big_chance_created": "Big Chances Created",
    "big_chance_missed":  "Big Chances Missed",
    "total_through_ball": "Through Balls",
    "clean_sheet":        "Clean Sheets",
    "saves":              "Saves",
    "yellow_card":        "Yellow Cards",
    "red_card":           "Red Cards",
    "fouls":              "Fouls",
    "total_offside":      "Offsides",
}


def get_seasons() -> dict[str, int]:
    """Return {label: id} for recent PL seasons."""
    r = requests.get(
        f"{_BASE}/competitions/1/compseasons?page=0&pageSize=10",
        headers=_HEADERS,
        timeout=10,
    )
    seasons = {}
    for s in r.json().get("content", []):
        label = s.get("label", "")
        sid = int(s.get("id", 0))
        if label and sid:
            seasons[label] = sid
    return seasons


def fetch_player_stats(season_id: int, page_size: int = 100) -> pd.DataFrame:
    """
    Fetch player stats for a given season from the PL API.
    Returns a tidy DataFrame with one row per player.
    """
    all_players: dict[int, dict] = {}

    for stat_key in STAT_TYPES:
        url = (
            f"{_BASE}/stats/ranked/players/{stat_key}"
            f"?page=0&pageSize={page_size}&compSeasons={season_id}"
            f"&comps=1&compCodeForActivePlayerFiltering=PL"
        )
        try:
            r = requests.get(url, headers=_HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            content = r.json().get("stats", {}).get("content", [])
        except Exception:
            continue

        for entry in content:
            owner = entry.get("owner", {})
            pid = int(owner.get("playerId", 0))
            if not pid:
                continue

            if pid not in all_players:
                name_obj = owner.get("name", {})
                name = (
                    name_obj.get("display", "")
                    if isinstance(name_obj, dict)
                    else str(name_obj)
                )
                all_players[pid] = {
                    "id": pid,
                    "name": name,
                    "position": owner.get("info", {}).get("positionInfo", ""),
                    "position_short": owner.get("info", {}).get("position", ""),
                    "shirt": int(owner.get("info", {}).get("shirtNum", 0) or 0),
                    "team": owner.get("currentTeam", {}).get("shortName", ""),
                    "nationality": owner.get("nationalTeam", {}).get("country", ""),
                }

            all_players[pid][stat_key] = float(entry.get("value", 0) or 0)

    df = pd.DataFrame(all_players.values())
    if df.empty:
        return df

    # Fill missing stat columns with 0
    for col in STAT_TYPES:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = df[col].fillna(0)

    # Derived stats
    df["90s"] = (df["mins_played"] / 90).clip(lower=0.01)
    df["goals_p90"]     = (df["goals"]              / df["90s"]).round(2)
    df["assists_p90"]   = (df["goal_assist"]         / df["90s"]).round(2)
    df["shots_p90"]     = (df["total_scoring_att"]   / df["90s"]).round(2)
    df["passes_p90"]    = (df["total_pass"]          / df["90s"]).round(0)
    df["tackles_p90"]   = (df["total_tackle"]        / df["90s"]).round(2)
    df["goal_involvements"] = df["goals"] + df["goal_assist"]
    df["shot_conversion"] = (
        (df["goals"] / df["total_scoring_att"].clip(lower=1)) * 100
    ).round(1)
    df["tackle_success"] = (
        (df["won_tackle"] / df["total_tackle"].clip(lower=1)) * 100
    ).round(1)

    df = df.sort_values("goals", ascending=False).reset_index(drop=True)
    return df
