import ast
import json
import os

from datetime import datetime
from sleeper.api.unofficial import UPlayerAPIClient
from sleeper.enum import Sport
from typing import List

def clean(s: str) -> str:
    """Cleans a string returned from a sleeper api call

    Parameters
    ----------
    s : str
        The raw string output from the sleeper api

    Returns
    -------
    str
        The cleaned output
    """

    replacements = {
        "null": "None",
        "false": "False",
        "true": "True",
    }

    for flag, replacement in replacements.items():
        s = s.replace(flag, replacement)

    return s


def get_roster_data(
    league_id: str,
) -> List[dict]:
    """Returns a list of roster data for a given league

    Parameters
    ----------
    league_id : str
        The league ID

    Returns
    -------
    List[dict]
        The roster data, with one entry for each team; keys owner_id, players (list[str])
    """
    # Check for current data
    if f"{league_id}_{datetime.now().strftime('%y%m%d')}.json" in os.listdir("data/roster_data/"):
        with open(f"data/roster_data/{league_id}_{datetime.now().strftime('%y%m%d')}.json") as file:
            return json.load(file)

    # Get raw data from API
    rosters = os.popen(f'curl "https://api.sleeper.app/v1/league/{league_id}/rosters"').read()
    rosters = clean(rosters)
    rosters = ast.literal_eval(rosters)

    # Extract relevant fields
    rosters = [
        {
            "owner_id": roster["owner_id"],
            "players": roster["players"],
        }
        for roster in rosters
    ]

    # Dump data
    with open(f"data/roster_data/{league_id}_{datetime.now().strftime('%y%m%d')}.json", "w") as file:
        json.dump(rosters, file)

    return rosters


def get_users(
    league_id: str,
) -> List[dict]:
    """Returns a list of users in a given league

    Parameters
    ----------
    league_id : str
        The league id number

    Returns
    -------
    List[dict]
        List of users; keys user_id, display_name
    """
    # Check for current data
    if f"{league_id}_{datetime.now().strftime('%y%m%d')}.json" in os.listdir("data/users/"):
        with open(f"data/users/{league_id}_{datetime.now().strftime('%y%m%d')}.json") as file:
            return json.load(file)
    
    # Get raw data from API
    users = os.popen(f'curl "https://api.sleeper.app/v1/league/{league_id}/users"').read()
    users = clean(users)
    users = ast.literal_eval(users)
    # Get display names and user_id
    users = [{"user_id": user["user_id"], "display_name": user["display_name"]} for user in users]

    # Dump data
    with open(f"data/users/{league_id}_{datetime.now().strftime('%y%m%d')}.json", "w") as file:
        json.dump(users, file)

    return users


def get_all_player_projections(
    week: int,
    scoring_type: str,
) -> List[dict]:
    """Returns a list of projections for all weeks/players (for weeks remaining in the season)

    Parameters
    ----------
    week : int
        Week number of the season
    scoring_type : str
        League scoring type; one of "PPR", "Half PPR", or "Standard"

    Returns
    -------
    List[dict]
        List of projections for each week/player; keys week, player_id, proj_score
    """
    # Check for current data
    if f"{datetime.now().strftime('%y%m%d')}.json" in os.listdir("data/projections/"):
        with open(f"data/projections/{datetime.now().strftime('%y%m%d')}.json") as file:
            return json.load(file)

    # Get data field name given scoring type
    score_field_name = {
        "PPR": "pts_ppr",
        "Half PPR": "pts_half_ppr",
        "Standard": "pts_std",
    }[scoring_type]

    # Get projections for the rest of the season
    all_player_projections = []
    for w in range(1, 18):
        all_player_projections.extend(
            UPlayerAPIClient.get_all_player_projections(
                sport=Sport.NFL,
                season=datetime.now().year,
                week=w,
            )
        )

    # Select relevant data
    all_player_projections = [
        {
            "week": proj.week,
            "player_id": proj.player_id,
            "proj_score": getattr(proj.stats, score_field_name),
        }
        for proj in all_player_projections
    ]

    # Restructure {player_id: [{week, proj_score}]}
    all_player_projections_restr = {
        player_id: []
        for player_id in set([projection["player_id"] for projection in all_player_projections])
    }
    for projection in all_player_projections:
        if projection["proj_score"] is not None and projection["proj_score"] > 0:
            all_player_projections_restr[projection["player_id"]].append({
                "week": projection["week"],
                "proj_score": projection["proj_score"],
            })

    # Dump data
    with open(f"data/projections/{datetime.now().strftime('%y%m%d')}.json", "w") as file:
        json.dump(all_player_projections_restr, file)

    return all_player_projections_restr


def get_all_players() -> dict:
    """Returns a list of all NFL players; used for accessing player names and positions from player_id

    Returns
    -------
    dict
        Dictionary of all NFL players; structure {player_id: {position: str, name: str}}
    """
    # Check for current data
    if f"{datetime.now().strftime('%y%m%d')}.json" in os.listdir("data/players/"):
        with open(f"data/players/{datetime.now().strftime('%y%m%d')}.json") as file:
            return json.load(file)

    # Get raw data from API
    players = os.popen('curl "https://api.sleeper.app/v1/players/nfl"').read()
    players = clean(players)
    players = ast.literal_eval(players)
    # Get display names and user_id
    players = {
        player_id: {
            "position": stats["fantasy_positions"][0] if stats["fantasy_positions"] is not None else "None",
            "name": f"{stats['first_name']} {stats['last_name']}"
        }
        for player_id, stats in players.items()
    }

    # Dump data
    with open(f"data/players/{datetime.now().strftime('%y%m%d')}.json", "w") as file:
        json.dump(players, file)

    return players