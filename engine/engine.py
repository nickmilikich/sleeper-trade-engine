import pandas as pd
import streamlit as st

from config import CONFIG
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
    max_group: int,
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
    max_group : int
        The maximum size of a trade group (e.g. if 2, trades can be of 1 or 2 players per team)

    Returns
    -------
    pd.DataFrame
        Data frame describing the best trade options for the user
    """

    # Get player projections
    projections_season = get_all_player_projections(week=week, scoring_type=scoring_type)
    # Filter to current/future projections
    projections_season = {
        player_id: [
            projection for projection in projections_season[player_id] if projection["week"] >= week
        ]
        for player_id in projections_season.keys()
    }
    
    # Get all players
    all_players = get_all_players()

    # Add position to projections
    projections_season = {
        player_id: [
            {
                "week": projection["week"],
                "proj_score": 0 if projection["proj_score"] is None else projection["proj_score"],
                "position": all_players[player_id]["position"]
            }
            for projection in projections
        ]
        for player_id, projections in projections_season.items()
    }

    # Drop projections for irrelevant positions
    projections_season = {
        k: v for k, v in projections_season.items()
        if v["position"].isin(CONFIG["rosters"]["single_positions"].keys())
    }

    # Get roster data
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
        free_agents=free_agents,
    )

    # Get user roster and other rosters
    user_roster = [roster for roster in rosters if roster["owner_id"] == user_id][0]
    rosters = [roster for roster in rosters if roster["owner_id"] != user_id]

    # Save user display name
    user_display_name = [u["display_name"] for u in league_users if u["user_id"] == user_id][0]

    trade_options = []
    # Loop through players on owner's roster
    combos = get_combos(user_roster["players"], max_group=max_group)
    progress_bar = st.progress(0)
    for i, players in enumerate(combos):
        # Loop through other rosters
        for j, other_roster in enumerate(rosters):
            # Loop through players in that other roster
            other_combos = get_combos(other_roster["players"], max_group=max_group)
            for k, other_players in enumerate(other_combos):
                progress_bar.progress(
                    i / len(combos) + j / len(combos) / len(rosters) + k / len(combos) / len(rosters) / len(other_combos),
                    text=f"Evaluating {', '.join([all_players[p]['name'] for p in players])} to {[l['display_name'] for l in league_users if l['user_id'] == other_roster['owner_id']][0]} for {', '.join([all_players[p]['name'] for p in other_players])}",
                )
                # Get proposed rosters with the trade
                proposed_user_roster = (set(user_roster["players"]) - set(players)).union(set(other_players))
                proposed_other_roster = (set(other_roster["players"]) - set(other_players)).union(set(players))
                # Save original projected scores
                user_orig_projection = user_roster["proj_score"]
                other_orig_projection = other_roster["proj_score"]
                # Get projected scores with the trade
                user_proposed_projection = get_projected_score(
                    players=list(proposed_user_roster) + free_agents,
                    projections=projections_season,
                )
                other_proposed_projection = get_projected_score(
                    players=list(proposed_other_roster) + free_agents,
                    projections=projections_season,
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
    if len(trade_options) > 0:
        trade_options["diff"] = trade_options[f"{user_display_name} Trade Projection"] - trade_options[f"{user_display_name} Previous Projection"]
        trade_options = trade_options.sort_values("diff", ascending=False, ignore_index=True)
        trade_options = trade_options.drop(columns="diff")

    return trade_options