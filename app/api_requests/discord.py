import os
import re
import requests

def get_guild_member_count(invite_url):
    # Extract the invite code from the URL using a regular expression
    invite_code_match = re.search(r"discord\.gg\/(\w+)", invite_url)
    invite_code = ""
    if invite_code_match:
        invite_code = invite_code_match.group(1)
    else:
        print("Error: Invalid Discord invite URL.")
        return None
    
    # Retrieve the client ID and secret from environment variables
    client_id = os.environ.get("DISCORD_CLIENT_ID")
    client_secret = os.environ.get("DISCORD_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Error: DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET environment variables are not set.")
        return None
    
    # Obtain an access token using the client ID and secret
    token_url = "https://discord.com/api/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "scope": "identify guilds"
    }
    auth = (client_id, client_secret)
    token_response = requests.post(token_url, data=data, auth=auth)
    
    if token_response.status_code == 200:
        access_token = token_response.json()["access_token"]
    else:
        print(f"Error obtaining access token: {token_response.status_code} - {token_response.text}")
        return None
    
    # Resolve the invite code to get the guild ID
    invite_url = f"https://discord.com/api/v10/invites/{invite_code}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    invite_response = requests.get(invite_url, headers=headers)
    
    if invite_response.status_code == 200:
        invite_data = invite_response.json()
        guild_id = invite_data.get("guild", {}).get("id")
        
        if guild_id:
            # Make the request to get the guild by ID
            guild_url = f"https://discord.com/api/v10/guilds/{guild_id}"
            params = {
                "with_counts": True
            }
            
            guild_response = requests.get(guild_url, headers=headers, params=params)
            
            if guild_response.status_code == 200:
                guild_data = guild_response.json()
                member_count = guild_data.get("approximate_member_count")
                return member_count
            else:
                print(f"Error retrieving guild data: {guild_response.status_code} - {guild_response.text}")
                return None
        else:
            print("Error: Guild ID not found in the invite data.")
            return None
    else:
        print(f"Error resolving invite code: {invite_response.status_code} - {invite_response.text}")
        return None
