import httpx
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("EBIRD_API_KEY")
region_code = "SG"
url = f"https://api.ebird.org/v2/data/obs/{region_code}/recent"
headers = {"x-ebirdapitoken": API_KEY}
params = {"back": 7}

def bird_sightings() -> str:
    """
    Returns a JSON object on all bird sightings in Singapore in the last 7 days
    """
    
    result = ""

    with httpx.Client() as client:
        response = client.get(url, headers=headers, params=params)
        response.raise_for_status()
        observations = response.json()

    for obs in observations:
        result += f"{obs['comName']} observed at {obs['locName']} on {obs['obsDt']}.\n"

    print(result);