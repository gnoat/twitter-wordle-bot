import schedule
from subprocess import run
import time
import pathlib
from configparser import ConfigParser
from datetime import datetime
from argparse import ArgumentParser
import os
import re
import tweepy


global wordle_num
configs = ConfigParser()
configs.read(pathlib.Path(__file__).parent / "configs.properties")


def infer_wordle_num(api):
    query = f"Wordle AND 6"
    wordle_str = r"Wordle ([0-9]+) \d*X*/6"
    all_wordle_nums = list()
    for tweet in api.search_tweets(q=query, result_type="recent", count=100):
        scores = re.findall(wordle_str, tweet.text)
        if (len(scores) > 0 and scores[0].isdigit()):
            all_wordle_nums.append(int(scores[0]))
    return max(all_wordle_nums)


def start_program(configs=configs):
    print(f"Wordle Num: {wordle_num}")
    prog_path = pathlib.Path(__file__).parent / "collect.py"
    run(f"python3 {str(prog_path)} --num {wordle_num} --y_height {int(configs['settings']['height'])}", shell=True)


def increase_wordle_num():
    wordle_num += 1
    print("New Wordle Num:", wordle_num)


if __name__ == "__main__":
    auth = tweepy.OAuthHandler(os.environ["TWT_API_KEY"], os.environ["TWT_API_SECRET"])
    auth.set_access_token(os.environ["TWT_TOKEN_KEY"], os.environ["TWT_TOKEN_SECRET"])
    api = tweepy.API(auth)
    parser = ArgumentParser(description="Collect Wordle results from Twitter")
    parser.add_argument(
        "-n",
        "--num",
        type=str,
        default="",
        help="Wordle puzzle number to score"
    )
    args = parser.parse_args()
    if args.num == "":
        wordle_num = infer_wordle_num(api)
    else:
        wordle_num = int(args.num)
    print("Starting first run...")
    start_program()
    schedule.every().day.at(configs['settings']['switch']).do(increase_wordle_num)
    schedule.every().day.at(configs['settings']['start']).do(start_program)

    while True:
        schedule.run_pending()
        time.sleep(1)
