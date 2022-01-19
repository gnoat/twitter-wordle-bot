import os
import pytest
import pathlib
import sys
import json


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
            f"test_results.json",
        ),
        "r",
    ) as f:
        return json.load(f)
