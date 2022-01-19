import re
import tweepy
import os
from collections import Counter
from statistics import median, mean, stdev
from functools import reduce
from argparse import ArgumentParser
from datetime import time
import time
from configparser import ConfigParser
import pathlib
import datetime


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
    "rs": "🟥"
}


def pull_results(api, wordle_num=None, result_dict=dict(), count=450):
    '''
    Runs a Twitter query, filters out tweets that don't contain a wordle, and adds the raw results to result_dict
    '''
    if (wordle_num is None) or (wordle_num == ""):
        wordle_num = "[0-9]+"
        query = "Wordle AND 6"
    else:
        query = f"Wordle AND {wordle_num} AND 6"
    wordle_str = f"Wordle {wordle_num} ([1-6]*X*)/6"
    for tweet in api.search_tweets(q=query, result_type="recent", count=count):
        scores = re.findall(wordle_str, tweet.text)
        if len(scores) > 0:
            result_dict[str(tweet.user.name)] = scores[0]
    return result_dict


def process_results(result_dict=dict(), height=6, max_n=0, raw_results=None):
    '''
    Take raw results which map user -> wordle score, aggregate scores, generate graph, and return graph and stats
    '''
    if raw_results is None:
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
    results_str = "\n".join(["".join(row) for row in list(zip(*results_matrix))[::-1]]) # Take the reverse transpose of the graph and convert to multiline string
    raw_nums = reduce(lambda a, b: a + b, [v * [int(k) if (k != "X") else 7] for k, v in raw_results.items()])
    median_raw = median(raw_nums)
    median_out = int(median_raw) if (int(median_raw) == median_raw) else round(median_raw, 1)
    return raw_results, results_str, round(median_out, 2), round(mean(raw_nums), 2), round(stdev(raw_nums), 2)


def create_messages(result_dict, height=6, wordle_num="ABC"):
    '''
    Take processed results and generate messages to Tweet
    '''
    rslts, img, med, avg, std = process_results(result_dict, height)
    top_msg = f"Wordle {wordle_num} {med}/6\n\n{img}\n\n*Sampled from {len(result_dict)} tweets"
    count_msg = "\n".join([f"{k} -> {rslts[k]}" for k in ["1", "2", "3", "4", "5", "6", "X"]])
    additional_msg = f"Mean: {avg}\nMedian: {med}\nStd: {std}\n\nRaw counts:\n{count_msg}"
    return top_msg, additional_msg


def infer_wordle_num(api):
    '''
    If wordle number isn't specified, infer it from a sample of the most recent tweets
    '''
    query = f"Wordle AND 6"
    wordle_str = r"Wordle ([0-9]+) \d*X*/6"
    all_wordle_nums = list()
    for tweet in api.search_tweets(q=query, result_type="recent", count=100):
        scores = re.findall(wordle_str, tweet.text)
        if (len(scores) > 0 and scores[0].isdigit()):
            all_wordle_nums.append(int(scores[0]))
    return max(all_wordle_nums)


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
        type=int,
        help="Wordle puzzle number to score"
    )
    parser.add_argument(
        "-y",
        "--y_height",
        type=int,
        default=8,
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
    parser.add_argument(
        "-m",
        "--max_wordle_num",
        type=int,
        help="Wordle num to stop collecting at.")
    parser.add_argument(
        "-q",
        "--query_count",
        type=int,
        default=150,
        help="Max number of tweets to query every wait period.")
    args = parser.parse_args()
    results_tracker = dict()
    hr = int(configs["settings"]["switch_days"].split(":")[0])
    mins = int(configs["settings"]["switch_days"].split(":")[1])
    switching_time = datetime.datetime.combine(datetime.date.today(), datetime.time(hr, mins))
    wordle_num = infer_wordle_num(api) if (args.num is None) else args.num
    if switching_time < datetime.datetime.now():
        switching_time += datetime.timedelta(days=1)
    print("Starting bot...")

    while(True if (args.max_wordle_num is None) else (wordle_num > args.max_wordle_num)): # Loop until max_wordle_num is reached
        while(datetime.datetime.now() < switching_time): # Loop until switch time from configs has passed
            print("Current time:", datetime.datetime.now())
            print("Ending time:", switching_time)
            updated_tracker = pull_results(api, wordle_num=wordle_num, result_dict=results_tracker, count=150) # pull and update results
            top_msg, additional_msg = create_messages(updated_tracker, height=args.y_height, wordle_num=wordle_num) # create messages from results
            print(top_msg)
            print(additional_msg)
            results_tracker = updated_tracker.copy() # update results tracker to include new results
            if args.continuous:
                print("Sending Tweets Continuous!")
                initial_response = api.update_status(status=top_msg)
                api.update_status(status=f"{configs['account']['name']}\n" + additional_msg, in_reply_to_status_id=initial_response.id)
            time.sleep(60 * args.wait)

        try:
            print("Sending Tweets!")
            initial_response = api.update_status(status=top_msg)
            api.update_status(status=f"{configs['account']['name']}\n" + additional_msg, in_reply_to_status_id=initial_response.id)
        except Exception as e:
                print("Exception:", e)

        # Once switch time has passed, increment wordle_num and switch time before restarting tweet collection
        wordle_num += 1
        switching_time += datetime.timedelta(days=1)