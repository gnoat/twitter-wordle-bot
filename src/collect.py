import re
import tweepy
import os
from collections import Counter
from statistics import median, mean, stdev
from functools import reduce
from argparse import ArgumentParser
from datetime import datetime
import time
from configparser import ConfigParser
import pathlib


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
    "rs": "🟥"
}


def update_results(api, wordle_num=None, result_dict=dict(), count=450):
    if (wordle_num is None) or (wordle_num == ""):
        wordle_num = "[0-9]+"
        query = "Wordle AND 6"
    else:
        query = f"Wordle AND {wordle_num} AND 6"
    wordle_str = f"Wordle {wordle_num} (\d*X*)/6"
    for tweet in api.search_tweets(q=query, result_type="recent", count=count):
        scores = re.findall(wordle_str, tweet.text)
        if len(scores) > 0:
            result_dict[str(tweet.user.name)] = scores[0]
    return result_dict


def process_results(result_dict, height=6, max_n=0):
    raw_results = Counter(result_dict.values())
    max_score = max(raw_results.values())
    max_score_key = max(raw_results, key=raw_results.get)
    results_matrix = list()
    normed_results = {k: max(max_n, round(height * raw_results.get(k, 0) / max_score)) for k in ["1", "2", "3", "4", "5", "6", "X"]}
    for row in ["1", "2", "3", "4", "5", "6", "X"]:
        if max_score_key == row:
            color = "gs"
        elif row == "X":
            color = "rs"
        else:
            color = "ys"
        current_row = [emoji_map[row]] + normed_results[row] * [emoji_map[color]] + (height - normed_results[row]) * [emoji_map["bs"]]
        results_matrix.append(current_row)
    raw_nums = reduce(lambda a, b: a + b, [v * [int(k) if (k != "X") else 7] for k, v in raw_results.items()])
    median_raw = median(raw_nums)
    median_out = int(median_raw) if (int(median_raw) == median_raw) else median_raw
    return raw_results, "\n".join(["".join(row) for row in list(zip(*results_matrix))[::-1]]), round(median_out, 2), round(mean(raw_nums), 2), round(stdev(raw_nums), 2)


def create_messages(result_dict, height=6, wordle_num="ABC"):
    rslts, img, med, avg, std = process_results(result_dict, height)
    top_msg = f"Wordle {wordle_num} {med}/6\n\n{img}\n\n*Sampled from {len(result_dict)} tweets"
    count_msg = "\n".join([f"{k} -> {rslts[k]}" for k in ["1", "2", "3", "4", "5", "6", "X"]])
    additional_msg = f"Mean: {avg}\nMedian: {med}\nStd: {std}\n\nRaw counts:\n{count_msg}"
    return top_msg, additional_msg


if __name__ == "__main__":
    # Read configs
    configs = ConfigParser()
    configs.read(pathlib.Path(__file__).parent / "configs.properties")

    # Authenticate to Twitter
    auth = tweepy.OAuthHandler(os.environ["TWT_API_KEY"], os.environ["TWT_API_SECRET"])
    auth.set_access_token(os.environ["TWT_TOKEN_KEY"], os.environ["TWT_TOKEN_SECRET"])
    api = tweepy.API(auth)

    # Parse arguments
    parser = ArgumentParser(description="Collect Wordle results from Twitter")
    parser.add_argument(
        "-n",
        "--num",
        type=str,
        default="",
        help="Wordle puzzle number to score"
    )
    parser.add_argument(
        "-y",
        "--y_height",
        type=int,
        default=7,
        help="Height of graph"
    )
    parser.add_argument(
        "-w",
        "--wait",
        type=int,
        default=5,
        help="Wait between searches in mins"
    )
    parser.add_argument(
        "-c",
        "--continuous",
        action="store_true",
        help="Update every iteration")
    args = parser.parse_args()
    results_tracker = dict()

    while(datetime.now().hour != int(configs["settings"]["start"].split(":")[0])):
        print("Current time:", datetime.now().hour)
        try:
            updated_tracker = update_results(api, wordle_num=args.num, result_dict=results_tracker, count=150)
            top_msg, additional_msg = create_messages(updated_tracker, height=args.y_height, wordle_num=args.num)
        except Exception as e:
            print("Exception:", e)
            continue
        results_tracker = updated_tracker.copy()
        print(top_msg)
        print(additional_msg)
        if args.continuous:
            print("Sending Tweets!")
            initial_response = api.update_status(status=top_msg)
            api.update_status(status=f"{configs['account']['name']}\n" + additional_msg, in_reply_to_status_id=initial_response.id)
        time.sleep(60 * args.wait)

    print("Sending Tweets!")
    initial_response = api.update_status(status=top_msg)
    api.update_status(status=f"{configs['account']['name']}\n" + additional_msg, in_reply_to_status_id=initial_response.id)