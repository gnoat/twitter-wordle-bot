import pytest
import sys
import os
import collector
from collections import Counter


def test_process_results(get_results):
    expected_graph = '''⬛⬛⬛🟩⬛⬛⬛
⬛⬛⬛🟩🟨⬛⬛
⬛⬛🟨🟩🟨⬛⬛
⬛⬛🟨🟩🟨⬛⬛
⬛⬛🟨🟩🟨🟨⬛
⬛🟨🟨🟩🟨🟨🟥
1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣❌'''

    raw_results, graph, med, avg, std = collector.process_results(get_results, background_color="bs")
    assert med == 4
    assert avg == 4.22
    assert std == 1.27
    assert raw_results == Counter({'4': 58, '5': 46, '3': 37, '6': 24, '2': 14, 'X': 6, '1': 2})
    assert graph == expected_graph


def test_query_to_message_pipeline(mock_twitter_api):
    additonal_msg_expected = '''Mean: 4.09
Median: 4
Std: 1.13

Raw counts:
1 -> 0
2 -> 5
3 -> 28
4 -> 29
5 -> 25
6 -> 8
X -> 2'''
    top_msg_expected = '''Wordle 216 4/6

⬜⬜🟨🟩⬜⬜⬜
⬜⬜🟨🟩🟨⬜⬜
⬜⬜🟨🟩🟨⬜⬜
⬜⬜🟨🟩🟨⬜⬜
⬜⬜🟨🟩🟨⬜⬜
⬜⬜🟨🟩🟨🟨⬜
⬜🟨🟨🟩🟨🟨⬜
1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣❌

*Sampled from 97 tweets'''

    api = mock_twitter_api
    configs = {
        'settings': {
            'switch_puzzles': '09:00',
            'error_wait': '10',
            'max_retries': '5',
            'cache_file': 'cache.json'
            }}
    updated_tracker = collector.pull_results(api, configs, wordle_num=216, result_dict=dict(), count=150) # pull and update results
    top_msg, additional_msg = collector.create_messages(updated_tracker, height=7, wordle_num=216, background_color="ws")
    assert top_msg.strip() == top_msg_expected
    assert additional_msg.strip() == additonal_msg_expected


def test_infer_wordle_num(mock_twitter_api):
    api = mock_twitter_api
    assert collector.infer_wordle_num(api) == 216