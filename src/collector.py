import tweepy
import os
import manager
from argparse import ArgumentParser
from configparser import ConfigParser
import pathlib


if __name__ == "__main__":
    # Read configs
    configs = ConfigParser()
    configs.read(pathlib.Path(__file__).parent / "configs.properties")

    # Authenticate to Twitter
    ext_vars = lambda s: os.environ[configs["external"][s]]
    auth = tweepy.OAuthHandler(ext_vars("TWT_API_KEY"), ext_vars("TWT_API_SECRET"))
    auth.set_access_token(ext_vars("TWT_TOKEN_KEY"), ext_vars("TWT_TOKEN_SECRET"))
    api = tweepy.API(auth)

    # Parse arguments
    parser = ArgumentParser(description="Collect Wordle results from Twitter")
    parser.add_argument(
        "-c",
        "--cache",
        action="store_true",
        help="Read cached results into memory when starting.",
    )
    parser.add_argument("-n", "--num", type=int, help="Wordle puzzle number to score.")
    parser.add_argument(
        "-y", "--y_height", type=int, default=8, help="Height of graph."
    )
    parser.add_argument(
        "-w", "--wait", type=int, default=5, help="Wait between searches in mins."
    )
    parser.add_argument(
        "-u",
        "--update_time",
        type=str,
        help="Time to send tweet to update with current scores.  If not specified, will only update at switching time.",
    )
    parser.add_argument(
        "-m", "--max_wordle_num", type=int, help="Wordle num to stop collecting at."
    )
    parser.add_argument(
        "-q",
        "--query_count",
        type=int,
        default=150,
        help="Max number of tweets to query every wait period.",
    )
    parser.add_argument(
        "-s",
        "--switch",
        type=str,
        default=configs["settings"]["switch_puzzles"],
        help="Time to switch to next Wordle puzzle num in format HH:MM.  Defaults to time in configuration if nothing is set.",
    )
    parser.add_argument(
        "-r",
        "--relative_time",
        action="store_true",
        help="Use relative time for switch time.  Defaults to absolute time if nothing is set.",
    )
    args = parser.parse_args()

    manager.main(api, configs, args)
