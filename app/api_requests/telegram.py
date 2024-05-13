import requests
import os


def get_supergroup_member_count(supergroup_name):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    url = f"https://api.telegram.org/bot{bot_token}/getChat"
    params = {"chat_id": f"@{supergroup_name}"}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["ok"]:
            member_count = data["result"]["members_count"]
            return member_count
        else:
            print(f"Failed to retrieve member count. Error: {data['description']}")
    else:
        print(f"Request failed with status code: {response.status_code}")

    return None
