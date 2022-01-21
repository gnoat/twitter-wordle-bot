import os
import pytest
import pathlib
import sys
import json


class TweetQuery:
    def __init__(self, user_id, text):
        self.text = text
        self.user = lambda s: s
        self.user.id = user_id


def pytest_sessionstart(session):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))


@pytest.fixture
def current_dir():
    return pathlib.Path(__file__).parent


@pytest.fixture
def get_results():
    with open(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            f"resources/mock_results.json",
        ),
        "r",
    ) as f:
        return json.load(f)


@pytest.fixture
def mock_twitter_api():
    class MockTwitterAPI:
        def __init__(self, *args, **kwargs):
            pass

        def search_tweets(*args, **kwargs):
            with open(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    f"resources/mock_query.json",
                ),
                "r",
            ) as f:
                return [TweetQuery(d["user"]["id"], d["text"]) for d in json.load(f)]

    return MockTwitterAPI()
