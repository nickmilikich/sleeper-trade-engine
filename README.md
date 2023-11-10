# sleeper-trade-engine

## Usage

- Clone the repo and navigate to the root
- Ensure you're running python3.11+
- If poetry isn't installed, `pip install poetry`
- `poetry install` to install the dependencies
- `poetry run streamlit run app.py` to run the applet

## Todo

Features
- Configure team composition from the frontend rather than the code (or even read directly from the APIs)
- Improve frontend experience (errors before selections are made)
- Automate emails with trade reports
- Allow flex in a trade being slightly unfavorable to the opponent

Technical
- Document this branch
- Modularize the `engine.py` functions a little