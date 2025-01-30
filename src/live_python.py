import requests 
from bs4 import BeautifulSoup
import re

def get_fight_info_from_fight_id(fight_id):
    """
    Input: 
        fight_id: str (The fight id of the fight on the ESPN
        website)
    
    Output: 
        fights: list (dict): list of dictionaries (each dictionary contains
        information about a fight)
        
    Purpose: 
        Extract the information from a fight given the fight_id 
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
    response = requests.get(fight_url, headers=headers, timeout=60)
    
    # raise an exception if not able to get fight data  
    if response.status_code != 200:
        print(f"Error: Could not retrieve page for fight ID {fight_id}")
        return None

    print(f"Success: Retrieved page for fight ID {fight_id}")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # TODO: check if live fight still has class mb6. If not, change
    fight_segments = soup.find_all("div", class_="mb6")
    fights = []
    
    # go through each of the fight card segments and get the fight information
    for fight in fight_segments:
        
        # continually update dictionary to store fight information
        # TODO: check if modify in-place or not
        fight_info = {}
        fight_info = get_fighter_names(fight, fight_info)
        fight_info = get_final_score(fight, fight_info)
        fight_info = get_round_victory_info(fight, fight_info)
        fight_info = get_fight_statistics(fight, fight_info)
        fights.append(fight_info)
    return fights


def get_fighter_names(fight, fight_info):
    """
    Input: 
        fight: BeautifulSoup Object(a fight segment from the ESPN fight page)
        fight_info (a dictionary to store the fight information)
    
    Output: 
        fight_info: dictionary with the fighter names
    
    Purpose:
        This function gets the names of the fighters in the fight
        and stores them in the fight_info dictionary
    """
    fighters = fight.find_all("span", class_="truncate tc db")
    fight_info["fighter1"] = {fighters[0].text: {}}
    fight_info["fighter2"] = {fighters[1].text: {}}
    return fight_info




def get_final_score(fight, fight_info):
    """
    Input: fight (a fight segment from the ESPN fight page)
    fight_info (a dictionary to store the fight information)
    
    Output: None
    
    This function gets the final score of the fight and stores
    it in the fight_info dictionary. It stores the round, time,
    method. It also adds a timestamp to the fight. 
    """
    pattern = re.compile(
        r"^Final(?P<method>(?:KO\/TKO|S Dec|U Dec|Sub|No Contest))"
        r"R(?P<round>\d+),\s*(?P<time>\d+:\d+)$"
    )
    
    def parse_fight_result(result_str):
        """
        Parse a fight result string of the form:
        - FinalKO/TKOR1, 3:38
        - FinalS DecR3, 5:00
        - FinalU DecR3, 5:00
        - FinalSubR1, 4:48
        and return (method, round, time).
        
        If the string does not match, return (None, None, None).
        """
        match = pattern.match(result_str.strip())
        if match:
            method = match.group("method")  # e.g. "KO/TKO", "S Dec", "U Dec", "Sub"
            round_num = "R" + match.group("round")  # e.g. "R1", "R3"
            fight_time = match.group("time")        # e.g. "3:38", "5:00"
            return method, round_num, fight_time
        else:
            return None, None, None
    
    fight_score = fight.find_all("div", class_="ScoreCell__Time Gamestrip__Time ScoreCell__Time--post clr-gray-01")
    
    method, round_num, fight_time = parse_fight_result(fight_score[0].find("div").text)
    fight_info["method"] = method
    fight_info["round"] = round_num 
    fight_info["time"] = fight_time
    fight_info["timestamp"] = (int(round_num[1]) - 1) * 5 * 60 + int(fight_time.split(":")[0]) * 60 + int(fight_time.split(":")[1])
    return fight_info

def get_round_victory_info(fight, fight_info):

    """
    Input: fight (a fight segment from the ESPN fight page)
    fight_info (a dictionary to store the fight information)
    
    Output: None
    
    Purpose: This function gets the round victory information
    for each fighter in the fight and stores it in the fight_info
    dictionary. 
    """
    fight_victory = fight.find_all(attrs={"data-testid": "gameStripBarVictory"})
    if fight_victory:
        fight_info["fighter_victory"] = fight_victory[0].text
    return fight_info


def get_fight_statistics(fight, fight_info):
    """
    Input: 
        fight (a fight segment from the ESPN fight page)
        fight_info (a dictionary to store the fight information)
    
    Output: 
        None
    
    Purpose: 
        This function gets the statistics for each fighter
        in the fight and stores it in the fight_info dictionary. 
    """
    fight_statistics = fight.find_all(attrs={"data-wrapping": "MMAMatchup"})
    for fight_statistic in fight_statistics:
        fight_list = fight_statistic.find_all("li")
        for fight_in_list in fight_list:
            lhs_rhs_values= fight_in_list.find_all("div", class_="MMAMatchup__Stat ns8 MMAMatchup__Stat__Text")
            lhs_rhs_array = [lhs_rhs_value.text for lhs_rhs_value in lhs_rhs_values] 
            fighter_1_value = lhs_rhs_array[0]
            fighter_2_value = lhs_rhs_array[1]
            key_for_information = fight_in_list.find_all("div", class_="ns9 fw-medium ttu nowrap clr-gray-04")[0].text
            fight_info["fighter1"][key_for_information] = fighter_1_value
            fight_info["fighter2"] [key_for_information] = fighter_2_value
    return fight_info
            

print(get_fight_info_from_fight_id(600040033))

    