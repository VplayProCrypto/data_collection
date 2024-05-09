import requests
import base64
import os
import tweepy


def get_user_public_metrics(username):
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")

    if not bearer_token:
        raise ValueError("Bearer token not found in environment variables")

    headers = {"Authorization": f"Bearer {bearer_token}"}

    params = {"user.fields": "public_metrics"}

    url = f"https://api.twitter.com/2/users/by/username/{username}"

    response = requests.get(url, headers=headers, params=params)
    print("Response Headers:", response.headers)
    print("Response Body:", response.text)
    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            public_metrics = data["data"]["public_metrics"]
            return public_metrics
        else:
            raise ValueError(f"User '{username}' not found")
    else:
        raise Exception(f"Request failed with status code {response.status_code}")


def test_tweepy(username):

    client = tweepy.Client(bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"))

    # Get Users

    # This endpoint/method returns a variety of information about one or more users
    # specified by the requested IDs or usernames

    user_ids = [2244994945, 6253282]

    # By default, only the ID, name, and username fields of each user will be
    # returned
    # Additional fields can be retrieved using the user_fields parameter
    response = client.get_users(ids=user_ids, user_fields=["public_metrics"])

    for user in response.data:
        print(user.username, user.public_metrics)
