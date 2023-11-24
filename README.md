# sleeper-trade-engine

## Usage

- Clone the repo and navigate to the root
- Ensure you're running python3.11+
- If poetry isn't installed, `pip install poetry`
- `poetry install` to install the dependencies

Run with GUI interface
- `poetry run streamlit run app.py` to run the applet

Generating and saving options data frame from command line
- `poetry run python -m generate_trades` + other arguments
    - Required
        - `-d` / `--dest` output destination path
        - `-l` / `--league_id` league ID
        - `-u` / `--username` user display name
        - `-w` / `--week` week
        - `-s` / `--scoring_type` scoring type
    - Optional
        - `--max_group` max trade group size
        - `--exclude` positions to exclude (e.g. `'["K", "DEF"]'`)

## Todo

Features
- Configure team composition from the frontend rather than the code (or even read directly from the APIs)
- Improve frontend experience (errors before selections are made)
- Automate emails with trade reports
- Allow flex in a trade being slightly unfavorable to the opponent
- Read current week from projections by default rather than selecting
- Allow user to configure trade sort order (benefit to user, mutual benefit factor, etc.)

Technical
- Modularize the `engine.py` functions a little