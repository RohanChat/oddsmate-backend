import requests 
from bs4 import BeautifulSoup


def get_fight_info_from_fighter_id(fight_id):
    """
    Input: fight_id (The fight id of the fight on the ESPN
    website)
    
    Output: A dataframe of information about the fight and each
    fighter
    """
    # Gets a fight url based on the fight id 
    
    fight_url = f"https://www.espn.com/mma/fightcenter/_/id/{fight_id}/league/ufc"
    
    
    # Set these headers to avoid being blocked by ESPN. ESPN
    # expects a broswer response so we need to fake it
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    # get a response from the fight url
    response = requests.get(fight_url, headers=headers)
    
    # raise an exception if not able to get fight 
    if response.status_code != 200:
        print(response)
        print(f"Error: Could not retrieve page for fight ID {fight_id}")
        return None
    else:
        print(f"Success: Retrieved page for fight ID {fight_id}")
        soup = BeautifulSoup(response.text, 'html.parser')
        fight_segments = soup.find_all("div", class_="mb6")
        fights = []
        for fight in fight_segments:
            fight_info = {}
            fight_info = get_fighter_names(fight, fight_info)
            fights.append(fight_info)
        return fights


def get_fighter_names(fight, fight_info):
    """
    Input: fight (a fight segment from the ESPN fight page)
    fight_info (a dictionary to store the fight information)
    
    Output: None
    
    This function gets the names of the fighters in the fight
    and stores them in the fight_info dictionary
    """
    fighters = fight.find_all("span", class_="truncate tc db")
    fight_info["fighter1"] = fighters[0].text
    fight_info["fighter2"] = fighters[1].text
    return fight_info


            

print(get_fight_info_from_fighter_id(600040033))

    