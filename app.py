import pandas as pd
import streamlit as st

from engine.engine import get_trade_options
from utils.data import get_users

st.title("Trade engine for Sleeper fantasy football leagues")

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

# Add refresh button (accepts a new dummy variable)
_ = st.button("Refresh")

# Get best trade options
trade_options = get_trade_options(
    league_id=league_id,
    user_id=user_id,
    week=week,
    scoring_type=scoring_type,
    league_users=league_users,
)
st.dataframe(trade_options)