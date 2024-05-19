import os
import re
import aiohttp


async def get_guild_member_count(invite_url):
    # Extract the invite code from the URL using a regular expression
    invite_code_match = re.search(r"discord\.com/invite/(\w+)", invite_url)
    invite_code = ""
    if invite_code_match:
        invite_code = invite_code_match.group(1)
    else:
        print("Error: Invalid Discord invite URL.")
        return None

    # Retrieve the bot token from the environment variable
    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    if not bot_token:
        print("Error: DISCORD_BOT_TOKEN environment variable is not set.")
        return None

    # Create an aiohttp session
    async with aiohttp.ClientSession() as session:
        # Make a request to the fetch_invite endpoint
        fetch_invite_url = f"https://discord.com/api/v10/invites/{invite_code}"
        headers = {"Authorization": f"Bot {bot_token}"}
        async with session.get(
            fetch_invite_url, headers=headers
        ) as fetch_invite_response:
            if fetch_invite_response.status == 200:
                invite_data = await fetch_invite_response.json()
                print(invite_data)
                guild_id = invite_data.get("guild", {}).get("id")
                if guild_id:
                    print(guild_id)
                    # Make a request to the get_guild endpoint to retrieve the member count
                    get_guild_url = f"https://discord.com/api/v10/guilds/{guild_id}"
                    params = {"with_counts": "true"}
                    async with session.get(
                        get_guild_url, headers=headers, params=params
                    ) as get_guild_response:
                        if get_guild_response.status == 200:
                            guild_data = await get_guild_response.json()
                            member_count = guild_data.get("approximate_member_count")
                            return member_count
                        else:
                            print(
                                f"Error retrieving guild data: {get_guild_response.status} - {await get_guild_response.text()}"
                            )
                            return None
                else:
                    print("Error: Guild ID not found in the invite data.")
                    return None
            else:
                print(
                    f"Error fetching invite data: {fetch_invite_response.status} - {await fetch_invite_response.text()}"
                )
                return None
