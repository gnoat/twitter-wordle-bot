#!/bin/bash

docker build -t twitter_wordle_bot .
docker run --env TWT_API_KEY --env TWT_API_KEY --env TWT_TOKEN_KEY --env TWT_TOKEN_KEY -d --rm twitter_wordle_bot