import copy

from config import CONFIG
from typing import List

def add_projected_scores(
    rosters: List[dict],
    projections: List[dict],
    all_players: List[dict],
) -> List[dict]:
    """Adds projected score for the remainder of the season as a key to a list of rosters

    Parameters
    ----------
    rosters : List[dict]
        List of rosters; keys owner_id and players (list of player_id)
    projections : List[dict]
        List of player/week projections; keys week, player_id, proj_score
    all_players : List[dict]
        List of all players in the league; structure [{player_id: {position: str, name: str}}]

    Returns
    -------
    List[dict]
        List of rosters with rest-of-season projected scored added as a key; keys owner_id, players, proj_score
    """
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
) -> float:
    """Gets the projected score for a given team of players

    Parameters
    ----------
    players : List[str]
        List of players available for a fantasy team
    projections : List[dict]
        List of player/week projections; keys week, player_id, proj_score
    all_players : List[dict]
        List of all players in the league; structure [{player_id: {position: str, name: str}}]

    Returns
    -------
    float
        The total projected rest-of-season score for the available roster of players
    """
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
    """Gets the projected score for a given roster of players for one week

    Parameters
    ----------
    projections : List[dict]
        List of projections for players of a given team / week; keys player_id, proj_score, week, position, name

    Returns
    -------
    float
        The projected score
    """
    score = 0.0
    projections_remaining = copy.deepcopy(projections)
    
    # Loop through roster positions
    for position, count in CONFIG["rosters"]["single_positions"].items():
        for _ in range(count):
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
    for position, count in CONFIG["rosters"]["flex_positions"].items():
        for _ in range(count):
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