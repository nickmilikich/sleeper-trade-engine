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

    # Get roster data
    rosters = get_roster_data(league_id)
    # Get player projections
    _, projections_season = get_all_player_projections(week=week, scoring_type=scoring_type)
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
                proposed_user_roster = (set(user_roster["players"]) - {player}).union({other_player})
                proposed_other_roster = (set(other_roster["players"]) - {other_player}).union({player})
                user_orig_projection = user_roster["proj_score"]
                other_orig_projection = other_roster["proj_score"]
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
                if user_proposed_projection > user_orig_projection and other_proposed_projection >= other_orig_projection:
                    trade_options.append({
                        "Sends": f"{all_players[player]['name']} ({all_players[player]['position']})",
                        "To": [u["display_name"] for u in league_users if u["user_id"] == other_roster["owner_id"]][0],
                        "Receives": f"{all_players[other_player]['name']} ({all_players[other_player]['position']})",
                        "User Previous Projection": round(user_orig_projection / (18 - week), 2),
                        "User Trade Projection": round(user_proposed_projection / (18 - week), 2),
                        "Other Previous Projection": round(other_orig_projection / (18 - week), 2),
                        "Other Trade Projection": round(other_proposed_projection / (18 - week), 2),
                    })

    trade_options = pd.DataFrame(trade_options)
    trade_options["diff"] = trade_options["User Trade Projection"] - trade_options["User Previous Projection"]
    trade_options = trade_options.sort_values("diff", ascending=False)
    trade_options = trade_options.drop(columns="diff")

    return trade_options