import requests
import os

def get_uaw_from_dappradar(dappradar_id: str, time_range: str):
    base_url = os.environ.get('DAPPRADAR_BASE_URL')
    api_key = os.environ.get('DAPPRADAR_API_KEY')
    
    response = requests.get(f"{base_url}/dapps/{dappradar_id}",
                            params={"range": time_range},
                            headers={
                                "accept": "application/json",
                                "x-api-key": api_key
                            })
    response.raise_for_status()
    return response.json()