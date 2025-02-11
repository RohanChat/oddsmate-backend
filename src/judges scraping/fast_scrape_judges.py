import asyncio
import json
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from unidecode import unidecode
from fuzzywuzzy import fuzz
from playwright.async_api import async_playwright

# ------------------------------------------------------------------------------
# Concurrency settings: Adjust this number based on your machine’s capacity.
# ------------------------------------------------------------------------------
CONCURRENCY_LIMIT = 5

# ------------------------------------------------------------------------------
# Async helper to fetch a page’s HTML using a headless browser
# ------------------------------------------------------------------------------
async def fetch_html(browser, url, semaphore):
    async with semaphore:
        try:
            # Open a new incognito context so that pages run independently.
            context = await browser.new_context(user_agent="Mozilla/5.0")
            page = await context.new_page()
            await page.goto(url)
            # Optionally, wait for network to be idle:
            # await page.wait_for_load_state('networkidle')
            html = await page.content()
            await context.close()
            return html
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

# ------------------------------------------------------------------------------
# Async version of parse_fight (originally synchronous)
# ------------------------------------------------------------------------------
async def async_parse_fight(browser, fight_url, semaphore):
    html = await fetch_html(browser, fight_url, semaphore)
    if html is None:
        print(f"Failed to retrieve fight page: {fight_url}")
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # --- Extract fighter names ---
    fighter_cells = soup.find_all('td', class_=['decision-top', 'decision-bottom'])
    fighter_names = []
    for cell in fighter_cells:
        a_tag = cell.find('a')
        if a_tag:
            fighter_names.append(unidecode(a_tag.get_text(strip=True)))
    if len(fighter_names) >= 2:
        fighter1, fighter2 = fighter_names[:2]
    else:
        fighter1, fighter2 = "", ""
        print(f"Could not extract both fighter names from {fight_url}")

    # --- Extract judges' scorecards ---
    judges_tables = soup.find_all('table', {'style': 'border-spacing: 1px; width: 100%'})
    if len(judges_tables) < 3:
        print(f"Expected at least 3 judges tables but found {len(judges_tables)} in {fight_url}")
        return None

    judges_results = {}
    for idx, table in enumerate(judges_tables[:3], start=1):
        judge_cell = table.find('td', class_='judge')
        if not judge_cell:
            print(f"Judge cell not found in table {idx} on {fight_url}")
            continue
        judge_name = unidecode(judge_cell.get_text(strip=True).split('\n')[0])
        rounds_data = []
        round_rows = table.find_all('tr', class_='decision')
        for row in round_rows:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            round_num = cells[0].get_text(strip=True)
            score_f1 = cells[1].get_text(strip=True)
            score_f2 = cells[2].get_text(strip=True)
            if score_f1 == '-' or score_f2 == '-':
                continue
            try:
                score_f1 = int(score_f1)
                score_f2 = int(score_f2)
            except ValueError:
                continue

            rounds_data.append({
                "round": round_num,
                "fighter1": score_f1,
                "fighter2": score_f2
            })

        totals = {}
        total_row = table.find('tr', class_='bottom-row')
        if total_row:
            total_cells = total_row.find_all('td')
            if len(total_cells) >= 3:
                total_f1 = total_cells[1].get_text(strip=True)
                total_f2 = total_cells[2].get_text(strip=True)
                try:
                    total_f1 = int(total_f1)
                    total_f2 = int(total_f2)
                    totals = {"fighter1": total_f1, "fighter2": total_f2}
                except ValueError:
                    totals = {}

        judges_results[f"Judge{idx}"] = {
            "judge_name": judge_name,
            "rounds": rounds_data,
            "total": totals
        }

    fight_data = {
        "fight_url": fight_url,
        "fighter1": fighter1,
        "fighter2": fighter2,
        "judges": judges_results
    }
    return fight_data

# ------------------------------------------------------------------------------
# Async version of get_ufcstats_events: fetch UFCStats events page concurrently.
# ------------------------------------------------------------------------------
async def async_get_ufcstats_events(browser, semaphore):
    url = "http://ufcstats.com/statistics/events/completed?page=all"
    html = await fetch_html(browser, url, semaphore)
    if html is None:
        print("Error fetching UFCStats events page")
        return []
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr", class_="b-statistics__table-row")
    events = []
    for row in rows:
        a_tag = row.find("a", class_="b-link")
        if not a_tag:
            continue
        event_link = a_tag.get("href", "").strip()
        if "/event-details/" not in event_link:
            continue
        event_id = event_link.split("/event-details/")[1]
        event_name = a_tag.get_text(strip=True)
        date_span = row.find("span", class_="b-statistics__date")
        if not date_span:
            continue
        event_date_str = date_span.get_text(strip=True)
        try:
            event_date = datetime.strptime(event_date_str, "%B %d, %Y")
        except Exception as e:
            print(f"Error parsing UFCStats event date '{event_date_str}': {e}")
            continue
        location_td = row.find("td", class_="b-statistics__table-col b-statistics__table-col_style_big-top-padding")
        event_location = location_td.get_text(strip=True) if location_td else ""
        events.append({
            "event_id": event_id,
            "event_name": event_name,
            "event_date": event_date,
            "event_date_str": event_date_str,
            "event_location": event_location
        })
    return events

# ------------------------------------------------------------------------------
# Async version of parse_event (originally synchronous)
# ------------------------------------------------------------------------------
async def async_parse_event(browser, event_url, semaphore):
    html = await fetch_html(browser, event_url, semaphore)
    if html is None:
        print(f"Failed to retrieve event page: {event_url}")
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # --- Extract event details ---
    event_info = {}
    top_row = soup.find('tr', class_='top-row')
    if top_row:
        td = top_row.find('td', class_='decision-top2')
        if td:
            parts = list(td.stripped_strings)
            if parts:
                event_info['name'] = parts[0]
                event_info['location'] = ", ".join(parts[1:]) if len(parts) > 1 else ""
            else:
                event_info['name'] = ""
                event_info['location'] = ""
    else:
        event_info['name'] = ""
        event_info['location'] = ""

    # --- Extract and reformat the event date ---
    bottom_row = soup.find('tr', class_='bottom-row')
    if bottom_row:
        td_date = bottom_row.find('td', class_='decision-bottom2')
        if td_date:
            date_str = td_date.get_text(strip=True)
            try:
                parsed_date = datetime.strptime(date_str, "%B %d, %Y")
                event_info['date'] = parsed_date.strftime("%d/%m/%Y")
            except Exception as e:
                print(f"Date parsing error for '{date_str}': {e}")
                event_info['date'] = date_str
        else:
            event_info['date'] = ""
    else:
        event_info['date'] = ""

    # --- Find all fight URLs in this event page ---
    fight_links = []
    fight_cells = soup.find_all('td', class_='list2')
    for cell in fight_cells:
        a_tag = cell.find('a', href=True)
        if a_tag and a_tag['href'].strip().startswith('decision/'):
            full_url = urljoin('https://mmadecisions.com/', a_tag['href'].strip())
            fight_links.append(full_url)
    # Remove duplicates
    fight_links = list(set(fight_links))

    # Process each fight concurrently
    fight_tasks = [
        asyncio.create_task(async_parse_fight(browser, fight_url, semaphore))
        for fight_url in fight_links
    ]
    fights_data = await asyncio.gather(*fight_tasks)
    fights_data = [f for f in fights_data if f is not None]

    # --- UFCStats event matching (if applicable) ---
    matched_event_id = None
    try:
        event_date = datetime.strptime(event_info.get("date", ""), "%d/%m/%Y")
    except Exception as e:
        print(f"Error parsing MMA Decisions event date '{event_info.get('date', '')}': {e}")
        event_date = None

    event_name = event_info.get('name', '')
    if 'UFC' in event_name and event_date:
        ufc_events = await async_get_ufcstats_events(browser, semaphore)
        best_score = -1
        for u_event in ufc_events:
            date_diff = abs((u_event["event_date"] - event_date).days)
            if date_diff <= 1:
                score = fuzz.token_set_ratio(u_event["event_location"], event_info.get("location", ""))
                if score > best_score:
                    best_score = score
                    matched_event_id = u_event["event_id"]
        if matched_event_id:
            print(f"Matched UFCStats event id {matched_event_id} (fuzzy score: {best_score}) for MMA Decisions event '{event_info.get('name', '')}'")
        else:
            print(f"No close UFCStats match found for MMA Decisions event '{event_info.get('name', '')}'")
    else:
        if not event_date:
            print("MMA Decisions event date unavailable; skipping UFCStats matching.")

    event_data = {
        "event_url": event_url,
        "event_details": event_info,
        "fights": fights_data
    }
    if matched_event_id:
        event_data["event_id"] = matched_event_id

    return event_data

# ------------------------------------------------------------------------------
# Async function to process all events in a given year range concurrently.
# ------------------------------------------------------------------------------
async def async_parse_all_events(browser, start_year=2025, end_year=2000, semaphore=None):
    if semaphore is None:
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    base_url = "https://mmadecisions.com/decisions-by-event/"
    event_tasks = []
    for year in range(start_year, end_year - 1, -1):
        year_url = f"{base_url}{year}/"
        print(f"\n--- Processing events for year: {year} ---")
        html = await fetch_html(browser, year_url, semaphore)
        if html is None:
            print(f"Failed to retrieve events page for {year}")
            continue
        soup = BeautifulSoup(html, 'html.parser')
        event_rows = soup.find_all('tr', class_='decision')
        for row in event_rows:
            event_cell = row.find('td', class_='list')
            if not event_cell:
                continue
            a_tag = event_cell.find('a', href=True)
            if a_tag:
                event_href = a_tag['href'].strip()
                full_event_url = urljoin('https://mmadecisions.com/', event_href)
                print(f"Found event URL: {full_event_url}")
                task = asyncio.create_task(async_parse_event(browser, full_event_url, semaphore))
                event_tasks.append(task)
    events_results = await asyncio.gather(*event_tasks)
    all_events = [e for e in events_results if e is not None]
    return all_events

# ------------------------------------------------------------------------------
# Async function to process only the latest event.
# ------------------------------------------------------------------------------
async def async_parse_latest_event(browser, semaphore):
    base_url = "https://mmadecisions.com/decisions-by-event/"
    html = await fetch_html(browser, base_url, semaphore)
    if html is None:
        print("Failed to retrieve events page")
        return None

    soup = BeautifulSoup(html, 'html.parser')
    event_row = soup.find('tr', class_='decision')
    if event_row:
        event_cell = event_row.find('td', class_='list')
        if event_cell:
            a_tag = event_cell.find('a', href=True)
            if a_tag:
                event_href = a_tag['href'].strip()
                full_event_url = urljoin('https://mmadecisions.com/', event_href)
                print(f"Processing latest event: {full_event_url}")
                return await async_parse_event(browser, full_event_url, semaphore)
    print("No events found")
    return None

# ------------------------------------------------------------------------------
# Main async function
# ------------------------------------------------------------------------------
async def main():
    # Create a semaphore to limit the number of concurrent pages.
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Example 1: Process the latest event
        # event_data = await async_parse_latest_event(browser, semaphore)
        # if event_data:
        #     with open('latest_event.json', 'w', encoding='utf-8') as f:
        #         json.dump(event_data, f, indent=2)
        #     print("Latest event data saved to latest_event.json")
        
        # Example 2: Process all events (adjust years as desired)
        all_events = await async_parse_all_events(browser, start_year=2021, end_year=1993, semaphore=semaphore)
        print(f"\nProcessed {len(all_events)} events.")
        with open("all_events.json", "w", encoding="utf-8") as f:
            json.dump(all_events, f, indent=2)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
