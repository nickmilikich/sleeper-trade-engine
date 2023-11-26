import ast
import copy
import numpy as np

from config import CONFIG
from typing import List

def add_projected_scores(
    rosters: List[dict],
    projections: dict,
    free_agents: List[str],
    all_players,
) -> List[dict]:
    """Adds projected score for the remainder of the season as a key to a list of rosters

    Parameters
    ----------
    rosters : List[dict]
        List of rosters; keys owner_id and players (list of player_id)
    projections : dict
        Dictionary mapping player_id to week, proj_score
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
    projections: dict,
    all_players,
) -> float:
    """Gets the projected score for a given team of players for the remainder of the season

    Parameters
    ----------
    players : List[str]
        List of players available for a fantasy team
    projections : dict
        Dictionary mapping player_id to week, proj_score

    Returns
    -------
    float
        The total projected rest-of-season score for the available roster of players
    """
    
    all_projections = copy.deepcopy(projections)

    # Filter projections to relevant roster of players
    projections = {
        player_id: projections.get(player_id, []) for player_id in players
    }
    
    # Restructure from {player_id: {week, proj_score, position}} to {week: {position: [proj_scores]}}
    projections_by_week = {
        week: {
            position: []
            for position in set([projection["position"] for player_projections in projections.values() for projection in player_projections])
        }
        for week in set([projection["week"] for player_projections in projections.values() for projection in player_projections])
    }
    for player_projections in projections.values():
        for projection in player_projections:
            projections_by_week[projection["week"]][projection["position"]].append(projection["proj_score"])

    # For each week, get projected team score
    projections_by_week = [
        get_one_projected_score(projections_by_week[week], week=week, projections=all_projections, all_players=all_players)
        for week in projections_by_week.keys()
    ]

    # Return sum of week scores
    return sum(projections_by_week)

def get_one_projected_score(
    projections_dict: dict,
    week,
    projections,
    all_players,
) -> float:
    """Gets the projected score for a given roster of players for one week

    Parameters
    ----------
    projections_dict : dict
        Dictionary of projected scores for that roster / week; maps position to list of proj_score

    Returns
    -------
    float
        The projected score
    """
    score = 0.0
    
    # print(f"all_players.keys() {len(all_players.keys())}")
    # print(f"projections.keys() {len(projections.keys())}")
    # print(f"overlap {len(set(all_players.keys()).intersection(set(projections.keys())))}")

    # Loop through roster positions
    for position, count in CONFIG["rosters"]["single_positions"].items():
        for _ in range(count):
            try:
                curr_score = max(projections_dict[position])
                score += curr_score
                projections_dict[position].remove(curr_score)

                relevant_projections = {
                    player: [
                        proj for proj in projections[player]
                        if proj["week"] == week
                        and proj["proj_score"] == curr_score
                    ]
                    for player in projections.keys()
                    if all_players[player]["position"] == position
                }
                relevant_projections = {
                    player: projs
                    for player, projs in relevant_projections.items()
                    if len(projs) > 0
                }
                print(f"Week {week} {[all_players[p]['name'] for p in relevant_projections.keys()]} ({curr_score})")
            except:
                pass

    # Loop through flex positions
    for position, count in CONFIG["rosters"]["flex_positions"].items():
        for _ in range(count):
            curr_scores = []
            for p in ast.literal_eval(position):
                curr_scores.extend(projections_dict.get(p, []))
            curr_score = max(curr_scores, default=0)
            score += curr_score
            projections_dict[[p for p in ast.literal_eval(position) if curr_score in projections_dict.get(p, [])][0]].remove(curr_score)
            
            relevant_projections = {
                player: [
                    proj for proj in projections[player]
                    if proj["week"] == week
                    and proj["proj_score"] == curr_score
                ]
                for player in projections.keys()
                if all_players[player]["position"] in ast.literal_eval(position)
            }
            relevant_projections = {
                player: projs
                for player, projs in relevant_projections.items()
                if len(projs) > 0
            }
            print(f"Week {week} {[all_players[p]['name'] for p in relevant_projections.keys()]} ({curr_score})")

    # print(f"Projected score for {projections_dict}: {score}")

    return score