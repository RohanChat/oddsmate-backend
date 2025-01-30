import requests 
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def load_all_fight_buttons(driver, max_clicks=10):
    """
    Input:
        driver: selenium webdriver
        max_clicks: int (maximum number of times to click the button)
        
    Output:
        None
        
    Purpose:
        This function clicks the "load more" button on the ESPN
        fight page until all fights are loaded or the maximum number
        of clicks is reached.
    
    Raises:
        Exception: If there is an error clicking the button
        Exception: If the button is not found after max_clicks
    """
    for _ in range(max_clicks):
        try:
            load_more_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='gameStripBarCaret']")))
            ActionChains(driver).move_to_element(load_more_button).click().perform()
        except Exception as e:
            print(f"Error: {e}")
            break
    else:
        print("No more fights to load or button not found.")

def get_fight_info_from_fight_id(html):
    """
    Input: 
        html: the html to parse from the selenium driver
    
    Output: 
        fights: list (dict): list of dictionaries (each dictionary contains
        information about a fight)
        
    Purpose: 
        Extract the information from a fight given the fight_id 
    """
    soup = BeautifulSoup(html, 'html.parser')
    
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
            

def run_process(fight_id):
    """
    Input:
        fight_id: str (the id of the fight to get information about)
        
    Output:
        None
    
    Purpose:
        This function gets the information about a fight given
        the fight_id and prints it out.
    """
    # service = Service(ChromeDriverManager().install())
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Helps bypass detection

    # Set up the driver
    service = Service(ChromeDriverManager().install())
    
    time.sleep(2)
    
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Start DevTools session
    driver.execute_cdp_cmd("Network.enable", {})

    # Set custom headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-US,en;q=0.9",
    }

    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

# Load the page
    
    try:
        url = f"https://www.espn.com/mma/fightcenter/_/id/{fight_id}/league/ufc"
        driver.get(url)
        load_all_fight_buttons(driver)
        html = driver.page_source
        fight_info = get_fight_info_from_fight_id(html)
        print(fight_info)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.close()
        driver.quit()

if __name__ == "__main__":
    fight_id = "600040033"
    run_process(fight_id)




    