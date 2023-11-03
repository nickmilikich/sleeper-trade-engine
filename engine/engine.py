import json
import os
import pandas as pd
import streamlit as st

from config import CONFIG
from datetime import datetime
from typing import List
from utils.combinatorics import get_combos
from utils.data import get_roster_data, get_all_player_projections, get_all_players
from utils.scoring import add_projected_scores, get_projected_score

def get_trade_options(
    league_id: str,
    user_id: str,
    week: int,
    scoring_type: str,
    league_users: List[dict],
) -> pd.DataFrame:
    """Gets a data frame of the best trade options for the user given the situation

    Parameters
    ----------
    league_id : str
        The league id number
    user_id : str
        The user id number
    week : int
        The current week of the season; used for calculating projected scores for remaining games
    scoring_type : str
        The league's scoring method; one of "PPR", "Half PPR", "Standard"
    league_users : List[dict]
        Information about the users in the league; keys user_id and display_name

    Returns
    -------
    pd.DataFrame
        Data frame describing the best trade options for the user
    """

    # Get player projections
    projections_season = get_all_player_projections(week=week, scoring_type=scoring_type)
    # Drop projections with no score
    projections_season = [
        projection for projection in projections_season
        if (projection["proj_score"] is not None) and (projection["proj_score"] is not None)
    ]
    
    # Get all players
    all_players = get_all_players()

    # Get roster data
    if f"{league_id}_{datetime.now().strftime('%y%m%d')}_w_projections.json" in os.listdir("data/roster_data/"):
        with open(f"data/roster_data/{league_id}_{datetime.now().strftime('%y%m%d')}_w_projections.json") as file:
            rosters = json.load(file)
        # Get free agents
        free_agents = [
            player_id for player_id in all_players.keys() if not any([
                player_id in roster["players"] for roster in rosters
            ]) and any([projection["proj_score"] > 0 for projection in projections_season if projection["player_id"] == player_id])
        ]
    else:
        rosters = get_roster_data(league_id)
        # Get free agents
        free_agents = [
            player_id for player_id in all_players.keys() if not any([
                player_id in roster["players"] for roster in rosters
            ])
        ]
        # Add projected scores to rosters
        rosters = add_projected_scores(
            rosters=rosters,
            projections=projections_season,
            all_players=all_players,
            free_agents=free_agents,
        )
        # Dump data
        with open(f"data/roster_data/{league_id}_{datetime.now().strftime('%y%m%d')}_w_projections.json", "w") as file:
            json.dump(rosters, file)

    # Get user roster and other rosters
    user_roster = [roster for roster in rosters if roster["owner_id"] == user_id][0]
    rosters = [roster for roster in rosters if roster["owner_id"] != user_id]

    # Save user display name
    user_display_name = [u["display_name"] for u in league_users if u["user_id"] == user_id][0]

    trade_options = []
    # Loop through players on owner's roster
    combos = get_combos(user_roster["players"], max_group=CONFIG["settings"]["max_group"])
    for players in combos:
        # Loop through other rosters
        for other_roster in rosters:
            with st.status(f"Evaluating {', '.join([all_players[p]['name'] for p in players])} to {[l['display_name'] for l in league_users if l['user_id'] == other_roster['owner_id']][0]}"):
                # Loop through players in that other roster
                other_combos = get_combos(other_roster["players"], max_group=CONFIG["settings"]["max_group"])
                for other_players in other_combos:
                    # Get proposed rosters with the trade
                    proposed_user_roster = (set(user_roster["players"]) - set(players)).union(set(other_players))
                    proposed_other_roster = (set(other_roster["players"]) - set(other_players)).union(set(players))
                    # Save original projected scores
                    user_orig_projection = user_roster["proj_score"]
                    other_orig_projection = other_roster["proj_score"]
                    # Check for obvious problems with the proposed trade to short-cut the projection calculations
                    if _initial_checks(
                        proposed_user_roster=proposed_user_roster,
                        proposed_other_roster=proposed_other_roster,
                        players=players,
                        other_players=other_players,
                        all_players=all_players,
                    ):
                        # Get projected scores with the trade
                        user_proposed_projection = get_projected_score(
                            players=list(proposed_user_roster) + free_agents,
                            projections=projections_season,
                            all_players=all_players,
                        )
                        other_proposed_projection = get_projected_score(
                            players=list(proposed_other_roster) + free_agents,
                            projections=projections_season,
                            all_players=all_players,
                        )
                        # If the trade is beneficial for the user and not harmful for the other
                        if user_proposed_projection > user_orig_projection and other_proposed_projection >= other_orig_projection:
                            # Save display names for other user involved in the trade
                            other_display_name = [u["display_name"] for u in league_users if u["user_id"] == other_roster["owner_id"]][0]
                            trade_options.append({
                                "Sends": ", ".join([f"{all_players[player]['name']} ({all_players[player]['position']})" for player in players]),
                                "To": other_display_name,
                                "Receives": ", ".join([f"{all_players[other_player]['name']} ({all_players[other_player]['position']})" for other_player in other_players]),
                                f"{user_display_name} Previous Projection": round(user_orig_projection / (18 - week), 2),
                                f"{user_display_name} Trade Projection": round(user_proposed_projection / (18 - week), 2),
                                "Other Previous Projection": round(other_orig_projection / (18 - week), 2),
                                "Other Trade Projection": round(other_proposed_projection / (18 - week), 2),
                            })

    # Sort the trade options by the size of the advantage it gives the user
    trade_options = pd.DataFrame(trade_options)
    trade_options["diff"] = trade_options[f"{user_display_name} Trade Projection"] - trade_options[f"{user_display_name} Previous Projection"]
    trade_options = trade_options.sort_values("diff", ascending=False, ignore_index=True)
    trade_options = trade_options.drop(columns="diff")

    return trade_options


def _initial_checks(
    proposed_user_roster: List[str],
    proposed_other_roster: List[str],
    players: List[str],
    other_players: List[str],
    all_players: dict,
) -> bool:
    # Make sure the proposed rosters are complete
    # Loop through roster positions
    for position, count in CONFIG["rosters"]["single_positions"].items():
        # If either proposed roster does not have enough of that position, do not pass initial checks
        if sum([all_players[player]["position"] == position for player in proposed_user_roster]) < count:
            return False
        if sum([all_players[player]["position"] == position for player in proposed_other_roster]) < count:
            return False

    return True