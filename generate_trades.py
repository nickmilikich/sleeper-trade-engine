import argparse
import ast

from datetime import datetime
from engine.engine import get_trade_options

def main():

    # Parse arguments
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-d", "--dest", help="Output destination")
    arg_parser.add_argument("-l", "--league_id", help="Sleeper league ID")
    arg_parser.add_argument("-u", "--username", help="Sleeper username")
    arg_parser.add_argument("-w", "--week", help="Week number")
    arg_parser.add_argument("-s", "--scoring_type", help="Scoring type")
    arg_parser.add_argument("--max_group", help="Maximum trade group size", default=2)
    arg_parser.add_argument("--exclude", help="Positions to exclude from analysis", default="[]")

    args = arg_parser.parse_args()

    # Get options
    trade_options = get_trade_options(
        league_id=args.league_id,
        user_id=args.username, # ID can be parsed if display name passed in
        week=int(args.week),
        scoring_type=args.scoring_type,
        max_group=int(args.max_group),
        exclude_positions=ast.literal_eval(args.exclude),
        status="terminal",
    )

    # Save results
    trade_options.to_csv(f"{args.dest}/{datetime.now().strftime('%y%m%d')}_report.csv", index=False)

if __name__ == "__main__":
    main()