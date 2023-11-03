import pandas as pd

from typing import List
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

    # Get roster data
    rosters = get_roster_data(league_id)
    # Get player projections
    projections_season = get_all_player_projections(week=week, scoring_type=scoring_type)
    # Get all players
    all_players = get_all_players()

    # Add projected scores to rosters
    rosters = add_projected_scores(
        rosters=rosters,
        projections=projections_season,
        all_players=all_players,
    )

    # Get user roster and other rosters
    user_roster = [roster for roster in rosters if roster["owner_id"] == user_id][0]
    rosters = [roster for roster in rosters if roster["owner_id"] != user_id]

    trade_options = []
    # Loop through players on owner's roster
    for player in user_roster["players"]:
        # Loop through other rosters
        for other_roster in rosters:
            # Loop through players in that other roster
            for other_player in other_roster["players"]:
                # Get proposed rosters with the trade
                proposed_user_roster = (set(user_roster["players"]) - {player}).union({other_player})
                proposed_other_roster = (set(other_roster["players"]) - {other_player}).union({player})
                # Save original projected scores
                user_orig_projection = user_roster["proj_score"]
                other_orig_projection = other_roster["proj_score"]
                # Get projected scores with the trade
                user_proposed_projection = get_projected_score(
                    players=proposed_user_roster,
                    projections=projections_season,
                    all_players=all_players,
                )
                other_proposed_projection = get_projected_score(
                    players=proposed_other_roster,
                    projections=projections_season,
                    all_players=all_players,
                )
                # If the trade is beneficial for the user and not harmful for the other
                if user_proposed_projection > user_orig_projection and other_proposed_projection >= other_orig_projection:
                    # Save display names for users involved in the trade
                    user_display_name = [u['display_name'] for u in league_users if u['user_id'] == user_id][0]
                    other_display_name = [u["display_name"] for u in league_users if u["user_id"] == other_roster["owner_id"]][0]
                    trade_options.append({
                        "Sends": f"{all_players[player]['name']} ({all_players[player]['position']})",
                        "To": other_display_name,
                        "Receives": f"{all_players[other_player]['name']} ({all_players[other_player]['position']})",
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