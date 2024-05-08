import requests
import os

def get_uaw_from_dappradar(dappradar_id: str, time_range: str) -> str:    
    response = requests.get(f"{os.environ.get('DAPPRADAR_BASE_URL')}/dapps/{dappradar_id}",
                            params={"range": time_range},
                            headers={
                                "accept": "application/json",
                                "x-api-key": os.environ.get('DAPPRADAR_API_KEY')
                            })
    response.raise_for_status()
    data = response.json()
    
    if data["success"]:
        uaw = data["results"]["metrics"]["uaw"]
        return str(uaw)
    else:
        return "Failed to retrieve UAW data."