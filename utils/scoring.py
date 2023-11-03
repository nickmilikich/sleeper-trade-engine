import copy

from config import CONFIG
from typing import List

def add_projected_scores(
    rosters: List[dict],
    projections: List[dict],
    all_players: List[dict],
) -> List[dict]:
    rosters = [
        {
            "owner_id": roster["owner_id"],
            "players": roster["players"],
            "proj_score": get_projected_score(roster["players"], projections, all_players)
        }
        for roster in rosters
    ]

    return rosters


def get_projected_score(
    players: List[str],
    projections: List[dict],
    all_players: List[dict],
):
    # Filter to relevant roster of players
    projections = [projection for projection in projections if projection["player_id"] in players]
    # Add position for each player
    projections = [
        {
            "player_id": projection["player_id"],
            "proj_score": projection["proj_score"],
            "week": projection["week"],
            "position": all_players[projection["player_id"]]["position"],
            "name": all_players[projection["player_id"]]["name"],
        }
        for projection in projections
    ]
    # For each week, get projected team score
    projections_by_week = [
        get_one_projected_score([projection for projection in projections if projection["week"] == week])
        for week in set([i["week"] for i in projections])
    ]
    # Return sum of week scores
    return sum(projections_by_week)

def get_one_projected_score(
    projections: List[dict],
) -> float:
    score = 0.0
    projections_remaining = copy.deepcopy(projections)
    
    # Loop through roster positions
    for position in CONFIG["rosters"]["single_positions"]:
        # Get relevant players for that position
        relevant_players = [
            projection
            for projection in projections_remaining
            if projection["position"] == position and projection["proj_score"] is not None
        ]
        # Sort by the highest scoring
        relevant_players = sorted(relevant_players, key=lambda x: x["proj_score"], reverse=True)
        # For the highest available, add the score and remove the player
        if len(relevant_players) > 0:
            score += relevant_players[0]["proj_score"]
            projections_remaining = [projection for projection in projections_remaining if projection["player_id"] != relevant_players[0]["player_id"]]

    # Loop through flex positions
    for position in CONFIG["rosters"]["flex_positions"]:
        # Get relevant players for that position
        relevant_players = [
            projection
            for projection in projections_remaining
            if projection["position"] in position and projection["proj_score"] is not None
        ]
        # Sort by the highest scoring
        relevant_players = sorted(relevant_players, key=lambda x: x["proj_score"], reverse=True)
        # For the highest available, add the score and remove the player
        if len(relevant_players) > 0:
            score += relevant_players[0]["proj_score"]
            projections_remaining = [projection for projection in projections_remaining if projection["player_id"] != relevant_players[0]["player_id"]]

    return score