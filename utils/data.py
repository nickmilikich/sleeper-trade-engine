import ast
import os

from datetime import datetime
from sleeper.api.unofficial import UPlayerAPIClient
from sleeper.enum import Sport
from typing import List, Tuple

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
    """Returns a dictionary of roster data for a given league

    Parameters
    ----------
    league_id : str
        The league ID

    Returns
    -------
    List[dict]
        The roster data, with one entry for each team
    """
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

    return rosters


def get_users(
    league_id: str,
) -> List[dict]:
    # Get raw data from API
    users = os.popen(f'curl "https://api.sleeper.app/v1/league/{league_id}/users"').read()
    users = clean(users)
    users = ast.literal_eval(users)
    # Get display names and user_id
    users = [{"user_id": user["user_id"], "display_name": user["display_name"]} for user in users]

    return users


def get_all_player_projections(
    week: int,
    scoring_type: str,
) -> Tuple[dict]:

    # Get data field name given scoring type
    score_field_name = {
        "PPR": "pts_ppr",
        "Half PPR": "pts_half_ppr",
        "Standard": "pts_std",
    }[scoring_type]

    # Get projections for the rest of the season
    all_player_projections = []
    for w in range(week, 18):
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
            "proj_score": eval(f"proj.stats.{score_field_name}"),
        }
        for proj in all_player_projections
    ]

    all_player_projections_week = [
        proj for proj in all_player_projections if proj["week"] == week
    ]

    return all_player_projections_week, all_player_projections


def get_all_players() -> List[dict]:
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

    return players