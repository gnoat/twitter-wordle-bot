import configparser
from pickle import NONE
import re
import tweepy
from collections import Counter
from statistics import median, mean, stdev, mode
from functools import reduce
import tweepy
from configparser import ConfigParser
from argparse import Namespace
from typing import Union, Tuple
import datetime
import time
import pathlib
import datetime
import json


# Easy way to map emojis to create graph
emoji_map = {
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "X": "❌",
    "bs": "⬛",
    "ws": "⬜",
    "gs": "🟩",
    "ys": "🟨",
    "rs": "🟥",
}


def twitter_query(
    api: tweepy.API, query: str, count: int, configs: ConfigParser
) -> tweepy.models.SearchResults:
    """
    Runs a Twitter query and returns the raw results
    """
    for _ in range(int(configs["settings"]["max_retries"])):
        try:
            tweets = api.search_tweets(q=query, result_type="recent", count=count)
            return tweets
        except tweepy.errors.TweepyException as e:
            print(f"~~~ Query Error: {e}")
            print(f"~~~ Waiting:", configs["settings"]["error_wait"], "mins...")
            time.sleep(int(configs["settings"]["error_wait"]) * 60)


def pull_results(
    api: tweepy.API,
    configs: ConfigParser,
    wordle_num: Union[int, str, None] = "",
    result_dict: dict = dict(),
    count: int = 450,
) -> dict:
    """
    Runs a Twitter query, filters out tweets that don't contain a wordle, and adds the raw results to result_dict
    """
    if (wordle_num is None) or (wordle_num == ""):
        wordle_num = "[0-9]+"
        query = "Wordle AND 6"
    else:
        query = f"Wordle AND {wordle_num} AND 6"
    wordle_str = f"Wordle {wordle_num} ([1-6]*X*)/6"
    tweets = twitter_query(api, query, count, configs)
    for tweet in tweets:
        scores = re.findall(wordle_str, tweet.text)
        if len(scores) > 0:
            result_dict[str(tweet.user.id)] = scores[0]
    return result_dict


def process_results(
    result_dict: dict = dict(),
    height: int = 6,
    max_n: int = 0,
    raw_results: Union[Counter, None] = None,
    background_color: str = "bs",
) -> Tuple[dict, str, int, float, float]:
    """
    Take raw results which map user -> wordle score, aggregate scores, generate graph, and return graph and stats
    """
    if raw_results is None:
        raw_results = Counter(result_dict.values())
    max_score = max(raw_results.values())
    max_score_key = max(raw_results, key=raw_results.get)
    results_matrix = list()
    normed_results = {
        k: max(max_n, round(height * raw_results.get(k, 0) / max_score))
        for k in ["1", "2", "3", "4", "5", "6", "X"]
    }
    for row in ["1", "2", "3", "4", "5", "6", "X"]:
        if max_score_key == row:
            color = "gs"
        elif row == "X":
            color = "rs"
        else:
            color = "ys"
        current_row = (
            [emoji_map[row]]
            + normed_results[row] * [emoji_map[color]]
            + (height - normed_results[row]) * [emoji_map[background_color]]
        )
        results_matrix.append(current_row)
    results_str = "\n".join(
        ["".join(row) for row in list(zip(*results_matrix))[::-1]]
    )  # Take the reverse transpose of the graph and convert to multiline string
    raw_nums = reduce(
        lambda a, b: a + b,
        [v * [int(k) if (k != "X") else 7] for k, v in raw_results.items()],
    )
    return (
        raw_results,
        results_str,
        round(median(raw_nums), 2),
        round(mean(raw_nums), 2),
        round(stdev(raw_nums), 2),
    )


def create_messages(
    result_dict: dict,
    height: int = 6,
    wordle_num: Union[int, str, None] = "",
    max_n: int = 0,
    background_color: str = "bs",
) -> Tuple[str, str]:
    """
    Take processed results and generate messages to Tweet
    """
    rslts, img, med, avg, std = process_results(
        result_dict, height, max_n=max_n, background_color=background_color
    )
    top_msg = f"Wordle {wordle_num} {int(med)}/6\n\n{img}\n\n*Sampled from {len(result_dict)} tweets"
    sample_count = sum(rslts.values())
    count_msg = "\n".join(
        [f"{k}: {round(100 * rslts[k] / sample_count, 1)}%" for k in ["1", "2", "3", "4", "5", "6", "X"]]
    )
    additional_msg = (
        f"Mean: {avg}\nMedian: {med}\nStd: {std}\n\nDistribution:\n{count_msg}"
    )
    return top_msg, additional_msg


def infer_wordle_num(api: tweepy.API):
    """
    If wordle number isn't specified, infer it from a sample of the most recent tweets
    """
    query = f"Wordle AND 6"
    wordle_str = r"Wordle ([0-9]+) \d*X*/6"
    all_wordle_nums = list()
    for tweet in api.search_tweets(q=query, result_type="recent", count=100):
        scores = re.findall(wordle_str, tweet.text)
        if len(scores) > 0 and scores[0].isdigit():
            all_wordle_nums.append(int(scores[0]))
    inferred = int(mode(all_wordle_nums))
    return inferred


def sort_times(hr_mins_str: str) -> datetime.datetime:
    """
    Sort a list of datetime.time objects by their hour, then minute
    """
    if hr_mins_str is None:
        return None
    hr = int(hr_mins_str.split(":")[0])
    mins = int(hr_mins_str.split(":")[1]) if len(hr_mins_str.split(":")) > 1 else 0
    switching_time = datetime.datetime.combine(
        datetime.date.today(), datetime.time(hr, mins)
    )
    if switching_time < datetime.datetime.now():
        switching_time += datetime.timedelta(days=1)
    return switching_time


def relative_times(hr_mins_str: str) -> datetime.datetime:
    """
    Return absolute time for relative time input
    """
    if hr_mins_str is None:
        return None, datetime.timedelta(minutes=0)
    hr = int(hr_mins_str.split(":")[0])
    mins = int(hr_mins_str.split(":")[1]) if len(hr_mins_str.split(":")) > 1 else 0
    delta = datetime.timedelta(hours=hr, minutes=mins)
    switching_time = datetime.datetime.now() + datetime.timedelta(hours=hr, minutes=mins)
    return switching_time, delta


def save_cache(
    result_dict: dict,
    configs: ConfigParser,
    to_cache: bool = True,
    wordle_num: Union[int, str, None] = "",
) -> dict:
    """
    Take processed results and cache them to disk
    """
    cache_file = pathlib.Path(__file__).parent / configs["settings"]["cache_file"]
    if to_cache:
        with open(cache_file, "w") as f:
            f.write(json.dumps({"wordle_num": wordle_num, "result_dict": result_dict}))
        print("~~~ Cached results for num", wordle_num)
        print("~~~ Cache saved to", cache_file)
    return result_dict.copy()


def read_cache(configs: ConfigParser) -> Tuple[Union[int, str, None], dict]:
    """
    Read cached results from disk
    """
    cache_file = pathlib.Path(__file__).parent / configs["settings"]["cache_file"]
    if cache_file.is_file():
        print("~~~ Reading cache from", cache_file)
        with open(cache_file, "r") as f:
            cache = json.loads(f.read())
        return (
            int(cache["wordle_num"]) if (cache["wordle_num"] is not None) else None,
            cache["result_dict"],
        )
    else:
        return None, dict()
