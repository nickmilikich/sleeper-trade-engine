import streamlit as st

from engine.engine import get_trade_options
from utils.data import get_users

st.title("Trade engine for Sleeper fantasy football leagues")

st.markdown("This app is designed to recommend trades for your Sleeper fantasy league.\
    First, paste your League ID (when you log in, the league ID can be found\
    in the URL: `sleeper.com/leagues/{league_id}/matchup`).\
    Then select your display name from within that league, the current week\
    (the trade engine works using projected scores between the current week\
    and the end of the season), and the scoring your league uses.\
    Wait a few minutes for calculation, and see the recommended trades.\n\
    Note: Results may be strange for current (games in-progress) weeks.\n\
    Note: The max trade size affects compute time *heavily*.\
    For example, trades of size 1 compute in about 5 minutes (depending on the week),\
    while trades of up to size 2 take several hours or more to compute.")

# Get league ID
league_id = st.text_input("League ID")

# Get user ID from list of users
league_users = get_users(league_id)
display_name = st.selectbox("Select your display name", [user["display_name"] for user in league_users])
user_id = [user["user_id"] for user in league_users if user["display_name"] == display_name][0]

# Get current week
week = st.selectbox("Select the current week", range(1, 18))

# Get scoring type
scoring_type = st.selectbox("Select scoring type", ["PPR", "Half PPR", "Standard"])

# Get scoring type
max_group = st.number_input("Max trade size", 1)

# Add refresh button (accepts a new dummy variable)
clicked = st.button("Calculate")

if clicked:
    # Get best trade options
    trade_options = get_trade_options(
        league_id=league_id,
        user_id=user_id,
        week=week,
        scoring_type=scoring_type,
        league_users=league_users,
        max_group=max_group,
    )
    st.dataframe(trade_options)
    clicked = False