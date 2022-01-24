from utils import (
    pull_results,
    create_messages,
    infer_wordle_num,
    sort_times,
    save_cache,
    read_cache,
    relative_times,
)
import tweepy
from configparser import ConfigParser
from argparse import Namespace
from datetime import time
import time
import datetime
from typing import Union


def main(api: tweepy.API, configs: ConfigParser, args: Namespace):
    # Some initial environment setup
    print("~ Environment setup...")
    results_tracker = dict()
    wordle_num = infer_wordle_num(api) if (args.num is None) else args.num
    print("~~~ Inferred Wordle number:", wordle_num)
    if args.relative_time:
        switching_time, switch_delta = relative_times(args.switch)
        update_time, update_delta = relative_times(args.update_time)
    else:
        switching_time = sort_times(args.switch)
        update_time = sort_times(args.update_time)
    if args.cache:
        cache_wordle_num, cache_results = read_cache(configs)
        if (cache_wordle_num is not None) and (
            (cache_wordle_num == args.num) or (args.num is None)
        ):
            wordle_num = cache_wordle_num
            results_tracker = cache_results
    print("~ Starting bot...")
    print("~ Wordle num:", wordle_num)

    # Main loop
    while (
        True if (args.max_wordle_num is None) else (wordle_num > args.max_wordle_num)
    ):  # Loop until max_wordle_num is reached
        while (
            datetime.datetime.now() < switching_time
        ):  # Loop until switch time from configs has passed

            print("~~ Current time:", datetime.datetime.now())
            print("~~ Ending time:", switching_time)
            print("~~ Update time:", update_time)

            updated_tracker = pull_results(
                api,
                configs,
                wordle_num=wordle_num,
                result_dict=results_tracker,
                count=150,
            )  # pull and update results
            top_msg, additional_msg = create_messages(
                updated_tracker, height=args.y_height, wordle_num=wordle_num
            )  # create messages from results
            print(top_msg)
            print(additional_msg)
            results_tracker = save_cache(
                results_tracker, configs, to_cache=args.cache, wordle_num=wordle_num
            )  # update results tracker to include new results

            if (args.update_time is not None) and (
                update_time < datetime.datetime.now()
            ):  # update time if specified

                print("~~ Sending Tweet Update!")

                top_msg, additional_msg = create_messages(
                    updated_tracker,
                    height=args.y_height,
                    wordle_num=wordle_num,
                    background_color="ws",
                )  # create messages from results
                initial_response = api.update_status(
                    status="Morning stats:\n\n" + top_msg
                )
                api.update_status(
                    status=f"{configs['account']['name']}\n" + additional_msg,
                    in_reply_to_status_id=initial_response.id,
                )
                if args.relative_time:
                    update_time += update_delta
                else:
                    update_time += datetime.timedelta(days=1)

            time.sleep(60 * args.wait)

        try:

            print("~~ Sending Tweets!")

            initial_response = api.update_status(status=top_msg)
            api.update_status(
                status=f"{configs['account']['name']}\n" + additional_msg,
                in_reply_to_status_id=initial_response.id,
            )

            # Once switch time has passed, increment wordle_num and switch time before restarting tweet collection
            results_tracker = dict()
            wordle_num += 1
            if args.relative_time:
                switching_time += switch_delta
            else:
                switching_time += datetime.timedelta(days=1)

            print("~~ Results tracker reset!")
            print("~~ Wordle num:", wordle_num)
            print("~~ Switching time:", switching_time)

        except Exception as e:

            print("Exception Sending Tweet:", e)
