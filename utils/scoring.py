import ast
import copy

from config import CONFIG
from typing import List

def add_projected_scores(
    rosters: List[dict],
    projections: List[dict],
    all_players: dict,
    free_agents: List[str],
) -> List[dict]:
    """Adds projected score for the remainder of the season as a key to a list of rosters

    Parameters
    ----------
    rosters : List[dict]
        List of rosters; keys owner_id and players (list of player_id)
    projections : List[dict]
        List of player/week projections; keys week, player_id, proj_score
    all_players : dict
        Dictionary of all players in the league; structure {player_id: {position: str, name: str}}
    free_agents : List[str]
        List of player_id of free agents in the league

    Returns
    -------
    List[dict]
        List of rosters with rest-of-season projected scored added as a key; keys owner_id, players, proj_score
    """
    rosters = [
        {
            "owner_id": roster["owner_id"],
            "players": roster["players"],
            "proj_score": get_projected_score(
                players=roster["players"] + free_agents,
                projections=projections,
                all_players=all_players,
            )
        }
        for roster in rosters
    ]

    return rosters


def get_projected_score(
    players: List[str],
    projections: List[dict],
    all_players: List[dict],
) -> float:
    """Gets the projected score for a given team of players for the remainder of the season

    Parameters
    ----------
    players : List[str]
        List of players available for a fantasy team
    projections : List[dict]
        List of player/week projections; keys week, player_id, proj_score
    all_players : dict
        Dictionary of all players in the league; structure {player_id: {position: str, name: str}}

    Returns
    -------
    float
        The total projected rest-of-season score for the available roster of players
    """
    
    # Filter projections to relevant roster of players
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

    # Sort by highest scoring
    projections_remaining = sorted(projections_remaining, key=lambda x: x["proj_score"], reverse=True)

    # Loop through roster positions
    for position, count in CONFIG["rosters"]["single_positions"].items():
        for _ in range(count):
            # Get relevant players for that position
            relevant_players = [
                projection
                for projection in projections_remaining
                if projection["position"] == position
            ]
            # # Sort by the highest scoring
            # relevant_players = sorted(relevant_players, key=lambda x: x["proj_score"], reverse=True)
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
                if projection["position"] in position
            ]
            # # Sort by the highest scoring
            # relevant_players = sorted(relevant_players, key=lambda x: x["proj_score"], reverse=True)
            # For the highest available, add the score and remove the player
            if len(relevant_players) > 0:
                score += relevant_players[0]["proj_score"]
                projections_remaining = [projection for projection in projections_remaining if projection["player_id"] != relevant_players[0]["player_id"]]

    # # Restructure projection {position: {player_id: proj_score}}
    # projections_dict = dict()
    # for position in set([projection["position"] for projection in projections_remaining]):
    #     projections_dict[position] = dict()
    # for projection in projections_remaining:
    #     projections_dict[projection["position"]][projection["player_id"]] = projection["proj_score"]

    # # Loop through roster positions
    # for position, count in CONFIG["rosters"]["single_positions"].items():
    #     for _ in range(count):
    #         # Get ID of highest scoring player, add it to score, and delete them
    #         if position in projections_dict.keys():
    #             max_player = max(projections_dict[position], key=projections_dict[position].get)
    #             score += projections_dict[position][max_player]
    #             del projections_dict[position][max_player]

    # # Loop through roster positions
    # for position, count in CONFIG["rosters"]["flex_positions"].items():
    #     for _ in range(count):
    #         # Get ID of highest scoring player, add it to score, and delete them
    #         projections_dict_flex = dict()
    #         for p in ast.literal_eval(position):
    #             if p in projections_dict.keys():
    #                 projections_dict_flex = {**projections_dict_flex, **projections_dict[p]}
    #         max_player = max(projections_dict_flex, key=projections_dict_flex.get)
    #         score += projections_dict_flex[max_player]
    #         player_position = [k for k, v in projections_dict.items() if max_player in v.keys()][0]
    #         del projections_dict[player_position][max_player]

    return score