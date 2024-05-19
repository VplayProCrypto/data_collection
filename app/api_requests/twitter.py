import requests
import base64
import os
import tweepy


def get_user_public_metrics(username):
    client = tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_SECRET"),
    )

    response = client.get_user(username)

    if response.data:
        return response.data
    else:
        return None
