import time
import re
from bs4 import BeautifulSoup
from pprint import pprint
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import asyncio
from playwright.async_api import async_playwright

#adding test line
class ESPNHistoricalScrapper():
    """
    A class to scrape historical UFC fight data from ESPN's fight center.
    """
    def __init__(self, headless=True, timeout=15000):
        """
        Input:
            headless: bool - Whether to run the browser through Playwright in headless mode.
            timeout: int - The maximum time to wait for a page to load before timing out.
        Output:
            None
        Purpose:
            Initializes the ESPNHistoricalScrapper class with default values.
        """
        self.start_year = 1993 
        self.end_year = 2026
        self.headless = headless 
        self.timeout = timeout 
        self.browser = None
        self.context = None 
        self.page = None 
        self.playwright = None
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
        self.extra_headers = {
            "Referer": "https://www.google.com/",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.fight_urls = []
        self.base_url = "https://www.espn.com/mma/fightcenter/_/league/ufc/year/{}"
        self.espn_base = "https://www.espn.com"
        self.fights = []
    
    
    def get_fight_urls(self):
        """
        Fetches all available fight URLs from ESPN's UFC fight center for the years 
        outlined as start and end years in the class. This will be used to parse
        fight information from each fight page.
        """
        print(f"[INFO] Starting to fetch list of urls from ESPN Fight Center for years {self.start_year}-{self.end_year}")
        for year in range(self.start_year, self.end_year):
            print(f"[INFO] Fetching fight URLs for year: {year}")
            self.page.goto(self.base_url.format(year), timeout=self.timeout)
            try:
                dropdown_selector = "select.dropdown__select"
                self.page.wait_for_selector(dropdown_selector, timeout=5000)
                self.page.click(dropdown_selector)  # Click the dropdown to ensure options load
                time.sleep(2)  # Allow some time for options to become visible
                html = self.page.content()
                soup = BeautifulSoup(html, "html.parser")
                
                select_element = soup.find_all("select", class_="dropdown__select", attrs={"style": "text-overflow:ellipsis;overflow:hidden;width:100%"})
                # print(select_element)
                if select_element:
                    for select in select_element:

                        options = select.find_all("option")
                        year_fight_urls = [self.espn_base + opt["data-url"] for opt in options if opt["data-url"] != "#"]     
                        self.fight_urls.extend(year_fight_urls)
                else:
                    print(f"[WARNING] No select element found for year {year}")
            except PlaywrightTimeout:
                print(f"[WARNING] No dropdown found for year {year}, skipping...")
                continue
            except Exception as e:
                print(f"[ERROR] An error occurred: {e}")
                continue
    
        # print(f"[INFO] Total fight URLs collected: {len(self.fight_urls)}")

    
    def get_historical_fight_info(self):
        """
        Srcapes historical fight data from ESPN's UFC fight center.
        """
        with sync_playwright() as self.playwright:
            # print("[DEBUG] Launching Chromium (headless)...")
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(
                user_agent=self.user_agent,
                extra_http_headers=self.extra_headers
            )
            self.page = self.context.new_page()
            print("[INFO] Getting fight URLs...")
            self.get_fight_urls()
            print("[INFO] All fight URLs processed successfully.")
            for fight_url in self.fight_urls:
                print(f"[INFO] Processing fight URL: {fight_url}")
                self.run_process(fight_url)
            self.browser.close()
            self.playwright.stop()
    
    def run_process(self, fight_url):
        """
        Input: 
            fight_url (str): URL of the ESPN fight page to scrape.
        Output:
            None
        Purpose:
            Main entry point to open the ESPN fight page via Playwright,
        """
        # print(f"[INFO] Target URL: {fight_url}")
        self.page.goto(fight_url, timeout=self.timeout)  # 15s timeout
        time.sleep(3)  # let page load
        self.load_all_fight_buttons(max_clicks=10)
        html = self.page.content()
        self.get_fight_info_from_fight_id(html)
        
    
    def load_all_fight_buttons(self, max_clicks=100):
        """
        Input:
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
        # print("\n[DEBUG] Start: load_all_fight_buttons")
        clicks_done = 0
        
        while clicks_done < max_clicks:
            try:
                # Find all visible 'Load More' buttons
                self.page.wait_for_selector("div[data-testid='gameStripBarCaret']", state="visible", timeout=3000)
                buttons = self.page.query_selector_all("div[data-testid='gameStripBarCaret']")
            except PlaywrightTimeout:
                print("[DEBUG] No 'Load More' buttons available. Stopping.")
                break

            if not buttons:
                # print("[DEBUG] No more 'Load More' buttons found.")
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
                    # print(f"[DEBUG] Clicked 'Load More' button #{clicks_done}")
                    time.sleep(1)
                except Exception as e:
                    print(f"[DEBUG] Error clicking button: {e}")
                    break

            # If none were clicked, stop
            if new_clicks == 0:
                # print("[DEBUG] No additional buttons clicked. Stopping.")
                break

            # Scroll to bottom to allow any new buttons to load below
            self.page.mouse.wheel(0, 999999)
            time.sleep(2)

            # Check if new buttons loaded  
            try:
                more_buttons = self.page.query_selector_all("div[data-testid='gameStripBarCaret']")
                if not more_buttons or len(more_buttons) == len(buttons):
                    # print("[DEBUG] No new 'Load More' buttons appeared. Stopping.")
                    break
            except Exception:
                break

        # print("[DEBUG] End: load_all_fight_buttons\n")
        
    def get_fight_info_from_fight_id(self, html):
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

        for fight in fight_segments:
            fight_info = {}
            fight_info = self.get_fighter_names(fight, fight_info)
            fight_info = self.get_final_score(fight, fight_info)
            fight_info = self.get_round_victory_info(fight, fight_info)
            fight_info = self.get_fight_statistics(fight, fight_info)
            pprint(fight_info, sort_dicts=False)  # nicely format the output
            self.fights.append(fight_info)
    
    def get_fighter_names(self, fight, fight_info):
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
        # print("[INFO] Getting fighter names...")
        fighters = fight.find_all("span", class_="truncate tc db")
        fight_info["fighter1"] = {fighters[0].text: {}}
        fight_info["fighter2"] = {fighters[1].text: {}}
        return fight_info

    def get_final_score(self, fight, fight_info):
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
        # print("[INFO] Getting final score...")
        fight_score = fight.find_all("div", class_="ScoreCell__Time Gamestrip__Time ScoreCell__Time--post clr-gray-01")
        method, round_num, fight_time = parse_fight_result(fight_score[0].find("div").text) if fight_score else (None, None, None)

        fight_info.update({"method": method, "round": round_num, "time": fight_time})
        # print("[INFO] Calculating timestamp...")
        if round_num and fight_time:
            try:
                round_index = int(round_num[1]) - 1
                mins, secs = map(int, fight_time.split(":"))
                fight_info["timestamp"] = round_index * 5 * 60 + mins * 60 + secs
            except ValueError:
                fight_info["timestamp"] = None
        return fight_info

    def get_round_victory_info(self, fight, fight_info):
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
        # print("[INFO] Getting round victory info...")
        fight_victory = fight.find_all(attrs={"data-testid": "gameStripBarVictory"})
        fight_info["fighter_victory"] = fight_victory[0].text if fight_victory else None
        return fight_info
    
    def get_fight_statistics(self, fight, fight_info):
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
        # print("[INFO] Getting fight statistics...")
        fight_statistics = fight.find_all(attrs={"data-wrapping": "MMAMatchup"})
        for fight_statistic in fight_statistics:
            fight_list = fight_statistic.find_all("li")
            for fight_in_list in fight_list:
                lhs_rhs_values = fight_in_list.find_all("div", class_="MMAMatchup__Stat ns8 MMAMatchup__Stat__Text")
                lhs_rhs_array = [lhs_rhs_value.text for lhs_rhs_value in lhs_rhs_values]
                if len(lhs_rhs_array) == 2:
                    fighter_1_value = lhs_rhs_array[0]
                    fighter_2_value = lhs_rhs_array[1]
                    key_for_information = fight_in_list.find_all("div", class_="ns9 fw-medium ttu nowrap clr-gray-04")[0].text
                    fighter_1_key = list(fight_info["fighter1"].keys())[0]
                    fighter_2_key = list(fight_info["fighter2"].keys())[0]
                    fight_info["fighter1"][fighter_1_key][key_for_information] = fighter_1_value
                    fight_info["fighter2"][fighter_2_key][key_for_information] = fighter_2_value
        return fight_info

    def kill_browser(self):
        """
        Input:
            None 
        Output:
            None
        Purpose:
            Kills the browser instance.
        """
        self.browser.close()
        self.playwright.stop()
        print("[INFO] Browser instance killed successfully.")
        return
        
        


class LiveESPNScraper():
    def __init__(self, headless=True, timeout=15000):
        """
        Input:
            headless: bool - Whether to run the browser through Playwright in headless mode.
            timeout: int - The maximum time to wait for a page to load before timing out.
        
        Output:
            None
        
        Purpose:
            Initializes the LiveESPNScraper class with default
            values.
        """
        self.base_url = "https://www.espn.com/mma/fightcenter/_/league/ufc/year/{}"
        self.fight_data = {}
        self.headless = headless
        self.timeout = timeout
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
        self.extra_headers = {
            "Referer": "https://www.google.com/",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.fight_info = {}
    
    async def monitor_fight(self):
        """
        This is an async function that will monitor a live fight on ESPN's fight center.
        
        Input:
            None
        
        Output:
            None
        
        Purpose:
            This function will open a browser instance, navigate to the ESPN fight center, and
            continuously monitor the fight details. It will print the fight details to the console
            every 2 seconds until the user stops the monitoring.
        
        Expected Output:
            None
        
        Sample Output:
            None 
        
        This function must be called with asyncio.run(live_scraper.monitor_fight())
        """
        async with async_playwright() as self.playwright:
            self.browser = await self.playwright.chromium.launch(headless=True)
            page = await self.browser.new_page()
            await page.goto(self.base_url)
            try:
                while True:
                    html = await page.content()
                    self.get_live_fight_info(html)
                    print("[INFO] Monitoring fight...", self.fight_info)
                    time.sleep(2)
                    print("[INFO] Reloading page...")
            except KeyboardInterrupt:
                print("Monitoring stopped.")
            finally:
                print("[INFO] Closing browser...")
                await self.browser.close()
                self.playwright.stop()
    
    def get_live_fight_info(self, html):
        """
        Input:
            html (str): HTML content of the ESPN fight page.
        Output:
            fight_data (dict): Dictionary containing fight details.
        Purpose:   
            Parses the HTML for the loaded ESPN fight page 
            and returns a list of fight dictionaries. This will be 
            updating live.
        Expected Output:
            A fight dictionary containing details of the live fight.
        Sample Output:
            get_fight_info_from_fight_id(html) -> 
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
            
            
        This will be updated to return a dictionary with the fight details.
        """
        soup = BeautifulSoup(html, 'html.parser')
        fight_segments = soup.find_all("div", class_="mb6")
        fight = fight_segments[0]


        self.fight_info = self.get_fighter_names(fight, self.fight_info)
        self.fight_info = self.get_curr_score(fight, self.fight_info)
        # fight_info = self.get_round_victory_info(fight, fight_info)
        self.fight_info = self.get_fight_statistics(fight, self.fight_info)
        pprint(self.fight_info, sort_dicts=False)  # nicely format the output
        return self.fight_info
    
    def get_fighter_names(self, fight, fight_info):
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
        # print("[INFO] Getting fighter names...")
        fighters = fight.find_all("span", class_="truncate tc db")
        fight_info["fighter1"] = {fighters[0].text: {}}
        fight_info["fighter2"] = {fighters[1].text: {}}
        return fight_info

    def get_round_victory_info(self, fight, fight_info):
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
        # print("[INFO] Getting round victory info...")
        fight_victory = fight.find_all(attrs={"data-testid": "gameStripBarVictory"})
        fight_info["fighter_victory"] = fight_victory[0].text if fight_victory else None
        return fight_info
    
    def get_curr_score(self, fight, fight_info):
        """ 
        Input:
            fight (BeautifulSoup object): HTML segment containing fight results.
            fight_info (dict): Dictionary to store fight details.
        Output:
            dict: Updated fight_info dictionary with method of victory, round, time, and timestamp.
        Purpose:
            Parses the live fight result details including method (e.g., KO/TKO, Decision),
            round, and fight duration. Additionally, it calculates the fight timestamp in seconds. This
            will update live 
        Expected Output:
            A dictionary where "method", "round", "time", and "timestamp" are extracted from the fight result.
            If the fight result is not found, values default to None.
        Sample Output:
            get_curr_score(fight, {}) -> {"method": "KO/TKO", "round": "R3", "time": "2:30", "timestamp": 810}
            get_curr_score(fight, {}) -> {"method": None, "round": None, "time": None, "timestamp":
        """
        pattern = re.compile(
            r"^Final(?P<method>(?:KO\/TKO|S Dec|U Dec|Sub|No Contest))"
            r"R(?P<round>\d+),\s*(?P<time>\d+:\d+)$"
        )
 
        live_pattern = re.compile(
            r"^(?:END\s+)?R(?P<round>\d+)(?:,\s*(?P<time>\d+:\d+))?$"
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
                - If the fight is finished (the string starts with "Final"), it is expected to follow the format:
                "FinalKO/TKO R2, 3:45" or "FinalU Dec R5, 5:00", where the method is captured.
                - Otherwise, for a live fight the string will be either "R3, 4:34" or "END R2". In that case,
                no method is provided, so we return None for the method.
                - If the string does not match any expected format, returns (None, None, None).
            
            Sample Output:
                parse_fight_result("FinalKO/TKO R3, 2:30") -> ("KO/TKO", "R3", "2:30")
                parse_fight_result("FinalU Dec R5, 5:00") -> ("U Dec", "R5", "5:00")
                parse_fight_result("R3, 4:34") -> (None, "R3", "4:34")
                parse_fight_result("END R2") -> (None, "R2", None)
                parse_fight_result("Invalid format") -> (None, None, None)
            """
            result_str = result_str.strip()
            if result_str.upper() == "PRE-FIGHT" or result_str.upper() == "WALKOUTS" or result_str.upper() == "INTROS":
                return (result_str.upper(), None, None)
            # print("---RESULT----", result_str)
            # Check if it's a finished fight by looking for "Final" at the beginning.
            if result_str.startswith("Final"):
                match = pattern.match(result_str)
                if match:
                    method = match.group("method")
                    round_str = "R" + match.group("round")
                    time_str = match.group("time")
                    return (method, round_str, time_str)
            else:
                # print("USING PATTERN", live_pattern)
                # Otherwise, try matching the live fight pattern.
                match = live_pattern.match(result_str)
                # print("----MATCH-----", match)
                if match:
                    # print("----MATCH ROUND-----", match.group("round"))
                    round_str = "R" + match.group("round")
                    time_str = match.group("time")  # Might be None if not provided.
                    # print("----MATCH TIME-----", match.group("time"))
                    # For live fights, method is not present.
                    return (None, round_str, time_str)

            # If neither pattern matched, return a default tuple.
            return (None, None, None)
            

        # print("----FIGHT SCORE LIVE----")
        fight_score = fight.find_all("div", class_="ScoreCell__Time Gamestrip__Time Gamestrip__Time--noOverview ScoreCell__Time--in clr-negative")
        method, round_num, fight_time = parse_fight_result(fight_score[0].text) if fight_score else (None, None, None)
        # if method is not None and round_num is not None and fight_time is not None:
        #     # print("----FIGHT SCORE LIVE----", method, round_num, fight_time)
            
        fight_info.update({"method": method, "round": round_num, "time": fight_time})

        if round_num and fight_time:
            try:
                round_index = int(round_num[1]) - 1
                mins, secs = map(int, fight_time.split(":"))
                fight_info["timestamp"] = round_index * 5 * 60 + mins * 60 + secs
            except ValueError:
                fight_info["timestamp"] = None
        return fight_info

    def get_fight_statistics(self, fight, fight_info):
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
        # print("[INFO] Getting fight statistics...")
        fight_statistics = fight.find_all(attrs={"data-wrapping": "MMAMatchup"})
        for fight_statistic in fight_statistics:
            fight_list = fight_statistic.find_all("li")
            for fight_in_list in fight_list:
                lhs_rhs_values = fight_in_list.find_all("div", class_="MMAMatchup__Stat ns8 MMAMatchup__Stat__Text")
                lhs_rhs_array = [lhs_rhs_value.text for lhs_rhs_value in lhs_rhs_values]
                if len(lhs_rhs_array) == 2:
                    fighter_1_value = lhs_rhs_array[0]
                    fighter_2_value = lhs_rhs_array[1]
                    key_for_information = fight_in_list.find_all("div", class_="ns9 fw-medium ttu nowrap clr-gray-04")[0].text
                    fighter_1_key = list(fight_info["fighter1"].keys())[0]
                    fighter_2_key = list(fight_info["fighter2"].keys())[0]
                    fight_info["fighter1"][fighter_1_key][key_for_information] = fighter_1_value
                    fight_info["fighter2"][fighter_2_key][key_for_information] = fighter_2_value
        return fight_info


if __name__ == "__main__":
    # historical_scraper = ESPNHistoricalScrapper()
    # historical_scraper.get_historical_fight_info()
    # live_scraper = LiveESPNScraper()
    # asyncio.run(live_scraper.monitor_fight())