import time
import re
from bs4 import BeautifulSoup
from pprint import pprint
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def get_fighter_names(fight, fight_info):
    """
    Input:
        fight (BeautifulSoup object): HTML segment containing fighter names.
        fight_info (dict): Dictionary to store fight details.
    
    Output:
        dict: Updated fight_info dictionary with extracted fighter names.
    
    Purpose:
        Extracts and stores the names of both fighters from the fight segment.
    
    Expected Output:
        A dictionary where "fighter1" and "fighter2" keys contain fighter names as nested keys.
        If no fighters are found, an empty dictionary is returned.
    
    Sample Output:
        get_fighter_names(fight, {}) -> {"fighter1": {"John Doe": {}}, "fighter2": {"Jane Smith": {}}}
    """
    fighters = fight.find_all("span", class_="truncate tc db")
    fight_info["fighter1"] = {fighters[0].text: {}}
    fight_info["fighter2"] = {fighters[1].text: {}}
    return fight_info


def get_final_score(fight, fight_info):
    """
    Input:
        fight (BeautifulSoup object): HTML segment containing fight results.
        fight_info (dict): Dictionary to store fight details.
    
    Output:
        dict: Updated fight_info dictionary with method of victory, round, time, and timestamp.
    
    Purpose:
        Parses the final fight result details including method (e.g., KO/TKO, Decision),
        round, and fight duration. Additionally, it calculates the fight timestamp in seconds.
    
    Expected Output:
        A dictionary where "method", "round", "time", and "timestamp" are extracted from the fight result.
        If the fight result is not found, values default to None.
    
    Sample Output:
        get_final_score(fight, {}) -> {"method": "KO/TKO", "round": "R3", "time": "2:30", "timestamp": 810}
        get_final_score(fight, {}) -> {"method": None, "round": None, "time": None, "timestamp": None}
    """
    pattern = re.compile(
        r"^Final(?P<method>(?:KO\/TKO|S Dec|U Dec|Sub|No Contest))"
        r"R(?P<round>\d+),\s*(?P<time>\d+:\d+)$"
    )

    def parse_fight_result(result_str):
        """
        Input:
            result_str (str): String containing fight result information.
        
        Output:
            tuple: (method of victory, round number, fight time) or (None, None, None) if not matched.
        
        Purpose:
            Extracts the fight result details (method, round, and time) from a given string using regex.
        
        Explanation:
            - Uses a regex pattern to match fight results that follow the format: "FinalKO/TKO R2, 3:45".
            - Extracts the method of victory (e.g., "KO/TKO", "U Dec"), round number, and fight time.
            - If the string does not match the expected format, returns (None, None, None).
        
        Sample Output:
            parse_fight_result("FinalKO/TKO R3, 2:30") -> ("KO/TKO", "R3", "2:30")
            parse_fight_result("FinalU Dec R5, 5:00") -> ("U Dec", "R5", "5:00")
            parse_fight_result("Invalid format") -> (None, None, None)
        """
        match = pattern.match(result_str.strip())
        return (match.group("method"), "R" + match.group("round"), match.group("time")) if match else (None, None, None)

    fight_score = fight.find_all("div", class_="ScoreCell__Time Gamestrip__Time ScoreCell__Time--post clr-gray-01")
    method, round_num, fight_time = parse_fight_result(fight_score[0].find("div").text) if fight_score else (None, None, None)

    fight_info.update({"method": method, "round": round_num, "time": fight_time})

    if round_num and fight_time:
        try:
            round_index = int(round_num[1]) - 1
            mins, secs = map(int, fight_time.split(":"))
            fight_info["timestamp"] = round_index * 5 * 60 + mins * 60 + secs
        except ValueError:
            fight_info["timestamp"] = None
    return fight_info

def get_round_victory_info(fight, fight_info):
    """
    Input:
        fight (BeautifulSoup object): HTML segment containing victory details.
        fight_info (dict): Dictionary to store fight details.
    
    Output:
        dict: Updated fight_info dictionary with the winning fighter's name.
    
    Purpose:
        Extracts and stores the fighter who won the fight.
    
    Expected Output:
        If the winning fighter is found, it will be stored in `fight_info["fighter_victory"]`.
        If no winner information is found, `fighter_victory` will be set to `None`.
    
    Sample Output:
        get_round_victory_info(fight, {}) -> {"fighter_victory": "Fighter Name"}
        get_round_victory_info(fight, {}) -> {"fighter_victory": None}
    """
    fight_victory = fight.find_all(attrs={"data-testid": "gameStripBarVictory"})
    fight_info["fighter_victory"] = fight_victory[0].text if fight_victory else None
    return fight_info

def get_fight_statistics(fight, fight_info):
    """
    Input:
        fight (BeautifulSoup object): HTML segment containing fight statistics.
        fight_info (dict): Dictionary to store fight details.
    
    Output:
        dict: Updated fight_info dictionary with statistics per fighter.
    
    Purpose:
        Parses fight statistics such as strikes landed, control time, and takedowns,
        and stores them under each fighter's name.
    
    Expected Output:
        A dictionary with fight statistics categorized under each fighter's name.
        If no statistics are found, an empty dictionary is returned.
    
    Sample Output:
        get_fight_statistics(fight, {}) -> {
            "fighter1": {"John Doe": {"Strikes Landed": "50", "Takedowns": "2"}},
            "fighter2": {"Jane Smith": {"Strikes Landed": "40", "Takedowns": "1"}}
        }
    """
    fight_statistics = fight.find_all(attrs={"data-wrapping": "MMAMatchup"})
    for fight_statistic in fight_statistics:
        fight_list = fight_statistic.find_all("li")
        for fight_in_list in fight_list:
            lhs_rhs_values = fight_in_list.find_all("div", class_="MMAMatchup__Stat ns8 MMAMatchup__Stat__Text")
            lhs_rhs_array = [lhs_rhs_values.text for lhs_rhs_values in lhs_rhs_values]
            if len(lhs_rhs_array) == 2:
                fighter_1_value = lhs_rhs_array[0]
                fighter_2_value = lhs_rhs_array[1]
                key_for_information = fight_in_list.find_all("div", class_="ns9 fw-medium ttu nowrap clr-gray-04")[0].text
                fighter_1_key = list(fight_info["fighter1"].keys())[0]
                fighter_2_key = list(fight_info["fighter2"].keys())[0]
                fight_info["fighter1"][fighter_1_key][key_for_information] = fighter_1_value
                fight_info["fighter2"][fighter_2_key][key_for_information] = fighter_2_value
    return fight_info


def load_all_fight_buttons(page, max_clicks=100):
    """
    Input:
        page (playwright.sync_api.Page): The Playwright page object.
        max_clicks (int): Maximum number of times to click the 'Load More' button.
    Output:
        None
    Purpose:
        Clicks the 'Load More' button on the ESPN fight page to load additional fights.
    Expected Output:
        None
    Sample Output: [In case of successful button clicks in console]
        (in console:
            [DEBUG] Clicked 'Load More' button #1
            [DEBUG] Clicked 'Load More' button #2
            [DEBUG] Timed out waiting for 'Scroll up' button. Stopping.
        )
    """
    print("\n[DEBUG] Start: load_all_fight_buttons")
    clicks_done = 0
    
    while clicks_done < max_clicks:
        try:
            # Find all visible 'Load More' buttons
            page.wait_for_selector("div[data-testid='gameStripBarCaret']", state="visible", timeout=3000)
            buttons = page.query_selector_all("div[data-testid='gameStripBarCaret']")
        except PlaywrightTimeout:
            print("[DEBUG] No 'Load More' buttons available. Stopping.")
            break

        if not buttons:
            print("[DEBUG] No more 'Load More' buttons found.")
            break

        # Click all currently visible buttons
        new_clicks = 0
        for btn in buttons[1:]:
            if clicks_done >= max_clicks:
                break
            try:
                btn.click()
                clicks_done += 1
                new_clicks += 1
                print(f"[DEBUG] Clicked 'Load More' button #{clicks_done}")
                time.sleep(1)
            except Exception as e:
                print(f"[DEBUG] Error clicking button: {e}")
                break

        # If none were clicked, stop
        if new_clicks == 0:
            print("[DEBUG] No additional buttons clicked. Stopping.")
            break

        # Scroll to bottom to allow any new buttons to load below
        page.mouse.wheel(0, 999999)
        time.sleep(2)

        # Check if new buttons loaded  
        try:
            more_buttons = page.query_selector_all("div[data-testid='gameStripBarCaret']")
            if not more_buttons or len(more_buttons) == len(buttons):
                print("[DEBUG] No new 'Load More' buttons appeared. Stopping.")
                break
        except Exception:
            break

    print("[DEBUG] End: load_all_fight_buttons\n")


def get_fight_info_from_fight_id(html):
    """
    Input:
        html (str): HTML content of the ESPN fight page.
    Output:
        list: List of dictionaries containing fight details.
    Purpose:
        Parses the final HTML for the loaded ESPN fight page 
        and returns a list of fight dictionaries.
    Expected Output:
        A list of dictionaries where each dictionary contains details of a fight.
    Sample Output:
        get_fight_info_from_fight_id(html) -> [
            {"fighter1": {"John Doe": {
                {'Pre-Fight Odds': '-260',
                             'KD': '0',
                             'TOT Strikes': '95/254',
                             'SIG Strikes': '92/250',
                             'Head': '56/196',
                             'Body': '25/34',
                             'Legs': '11/20',
                             'Control': '0:50',
                             'Take Downs': '0/6',
                             'SUB ATT': '0'}
                }
                }}, 
                "fighter2": 
                {"Jane Smith": {
                    {'Pre-Fight Odds': '-260',
                             'KD': '0',
                             'TOT Strikes': '95/254',
                             'SIG Strikes': '92/250',
                             'Head': '56/196',
                             'Body': '25/34',
                             'Legs': '11/20',
                             'Control': '0:50',
                             'Take Downs': '0/6',
                             'SUB ATT': '0'}
                    }
                    }
                }, "method": "KO/TKO", "round": "R3", "time": "2:30", "timestamp": 810},
        ]
    """
    soup = BeautifulSoup(html, 'html.parser')
    fight_segments = soup.find_all("div", class_="mb6")
    fights = []

    for fight in fight_segments:
        fight_info = {}
        fight_info = get_fighter_names(fight, fight_info)
        fight_info = get_final_score(fight, fight_info)
        fight_info = get_round_victory_info(fight, fight_info)
        fight_info = get_fight_statistics(fight, fight_info)
        fights.append(fight_info)
    return fights


def run_process(fight_id):
    """
    Input: 
        fight_id (str): The unique identifier for the fight.
    Output:
        None
    Purpose:
        Main entry point to open the ESPN fight page via Playwright, 
        click all 'Load more' buttons, parse data, and print results.
    """
    url = f"https://www.espn.com/mma/fightcenter/_/id/{fight_id}/league/ufc"
    print(f"[INFO] Starting Playwright for fight_id={fight_id}")
    print(f"[INFO] Target URL: {url}")

    with sync_playwright() as p:
        # 1) Launch a headless browser
        print("[DEBUG] Launching Chromium (headless)...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            extra_http_headers={
                "Referer": "https://www.google.com/",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        page = context.new_page()

        # 2) Go to the ESPN fight page
        print("[DEBUG] Navigating to page...")
        page.goto(url, timeout=15000)  # 15s timeout

        time.sleep(3)  # let page load
        # 3) Click the 'load more fights' button multiple times
        load_all_fight_buttons(page, max_clicks=100)

        # 4) Extract HTML and parse
        print("[DEBUG] Extracting final page content for parsing.")
        html = page.content()
        fights_data = get_fight_info_from_fight_id(html)

        # 5) Close the browser
        browser.close()

    print("[INFO] Fights Data Parsed Successfully. Here is the result:")
    pprint(fights_data, sort_dicts=False)  # nicely format the output


if __name__ == "__main__":
    fight_id = "600040033"
    run_process(fight_id)


# TODO: be able to extract all the fight_id's from the site to run multiple times and dump data into a database


