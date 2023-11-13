import pandas as pd
import streamlit as st

from config import CONFIG
from datetime import datetime
from engine.engine import get_trade_options, evaluate_scenario
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
    while trades of up to size 2 take several hours or more to compute.\
    Dropping some positions from analysis, for example K or DEF, can speed up\
    computation time.")

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

# Select any positions to exclude from analysis
exclude_positions = st.multiselect("Select any positions to exclude from analysis", CONFIG["rosters"]["single_positions"])

col1, col2 = st.columns(2)

with col1:
    with st.form("Generate scenarios"):
        generate_scenarios = st.form_submit_button("Generate scenarios")
        if generate_scenarios:
            # Get best trade options
            trade_options = get_trade_options(
                league_id=league_id,
                user_id=user_id,
                week=week,
                scoring_type=scoring_type,
                max_group=max_group,
                league_users=league_users,
                exclude_positions=exclude_positions,
            )
            st.session_state["trade_options"] = trade_options
    print(st.session_state.to_dict())
    trade_options = st.session_state.get("trade_options", pd.DataFrame({}))
    st.download_button(
        label="Download this data",
        data=trade_options.to_csv().encode("utf-8"),
        file_name=f"{datetime.now().strftime('%y%m%d')}_report.csv",
    )
    st.dataframe(trade_options)

with col2:
    with st.form("Input scenario"):
        input_scenario = st.form_submit_button("Test a scenario")
        if input_scenario:
            # Evaluate scenario
            result = evaluate_scenario(
                league_id=league_id,
                user_id=user_id,
                week=week,
                scoring_type=scoring_type,
                league_users=league_users,
                user_display_name=display_name,
            )
            st.markdown(f"{display_name} score goes from {round(result['user'][0], 2)} to {round(result['user'][1], 2)} (change of {round(result['user'][1] - result['user'][0], 2)})")
            st.markdown(f"{result['other_display_name']} score goes from {round(result['other'][0], 2)} to {round(result['other'][1], 2)} (change of {round(result['other'][1] - result['other'][0], 2)})")