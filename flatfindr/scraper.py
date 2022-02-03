# facebook marketplace
import json
import os
import pickle
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from flatfindr.logins import LOGINS
from flatfindr.utils import KEYWORDS, URL

ONE_WEEK = 8
MAX_ITEMS = 30


class Scraper:
    def __init__(
        self,
        website,
        headless=False,
        db_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            os.path.join("raw_data", "db.json"),
        ),
    ):
        self.website = website
        self.email = LOGINS.get(website, {}).get("id", "id")
        self.password = LOGINS.get(website, {}).get("pass", "pass")
        self.db_path = db_path
        self.load_driver(headless=headless)
        self.main_url = URL.get(website)
        self.items_links = []
        self.load_db()

    def load_driver(self, headless=False, docker=False):
        # Handle the 'Allow notifications box':
        option = Options()
        option.add_argument("--disable-infobars")
        option.add_argument("start-maximized")
        option.add_argument("--disable-extensions")
        if headless or docker:
            option.add_argument("--headless")
        if docker:
            option.add_argument("--disable-gpu")
            option.add_argument("window-size=1024,768")
            option.add_argument("--no-sandbox")
        # Pass the argument 1 to allow and 2 to block
        option.add_experimental_option(
            "prefs", {"profile.default_content_setting_values.notifications": 2}
        )
        if docker:
            self.driver = webdriver.Chrome(
                options=option,
                executable_path=os.path.join(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                    "chromedriver-linux64",
                ),
            )
        else:
            self.driver = webdriver.Chrome(
                options=option,
                executable_path=os.path.join(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                    "chromedriver",
                ),
            )

    def quit_driver(self):
        self.driver.quit()

    def save_cookies(self):
        cookies_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            f"raw_data/cookies-{self.website}.pkl",
        )
        with open(cookies_path, "wb") as cookies_file:
            pickle.dump(self.driver.get_cookies(), cookies_file)

    def load_cookies(self):
        self.driver.get(self.main_url)
        cookies_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            f"raw_data/cookies-{self.website}.pkl",
        )
        with open(cookies_path, "rb") as cookies_file:
            cookies = pickle.load(cookies_file)
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    def item_details_to_string(self, item_details):
        sentence = ""
        for key, value in item_details.items():
            if key not in ("images", "state"):
                sentence += f"{key}: {value} \n"
        sentence += "\n  " + "=" * 40 + "\n  " + "=" * 40 + "\n"
        return sentence

    def item_details_to_html(self, item_details):
        sentence = ""
        for key, value in item_details.items():
            if key not in ("images", "state"):
                if key == "url":
                    sentence += f"{key}: <a target='_blank' href='{value}'>{value[-15:-1]}</a> \n"
                elif key == "address":
                    href = f"""https://www.google.com/maps/place/{value.replace(" ", "+").replace("'", "+")},{KEYWORDS["gmaps"]}"""
                    sentence += (
                        f"{key}: <a target='_blank' href='{href}'>{value}</a> \n"
                    )
                elif key == "price":
                    sentence += f"{key}: {value} $ \n"
                elif key == "surface":
                    sentence += f"{key}: {value} m² \n"
                else:
                    sentence += f"{key}: {value} \n"
        return sentence

    def is_old(self, item_details):
        return (
            item_details.get("published")
            == (date.today() - timedelta(days=ONE_WEEK)).isoformat()
        )

    def is_duplicate(self, item_details):
        all_description = [data[-1] for data in self.db["data"] if data[-1] != ""]
        return item_details.get("description") in all_description

    def is_swap(self, item_details):
        return any(
            swap in item_details.get("description", "").lower()
            for swap in ("swap", "transfer", "échange", "exchange")
        )

    def is_first_floor(self, item_details):
        return any(
            ff in item_details.get("description", "").lower()
            for ff in (
                "ground floor",
                "first floor",
                "rdc",
                "rez-de-chaussée",
                "rez de chaussée",
            )
        )

    def get_item_details(self, item_url):
        item_details = {}
        item_details["url"] = item_url
        self.driver.get(item_url)
        return item_details

    def get_items_details(self, max_items=30, to_html=False):
        items_details = []
        if len(self.items_links):
            cnt = 0
            for item_url in self.items_links[:max_items]:
                item_details = self.get_item_details(item_url)
                self.db["data"].append(
                    [item_details.get(feature, "") for feature in self.db["columns"]]
                )
                if item_details.get("state") == "new":
                    # If the ad is interesting, we add its string description for the bot to display
                    if to_html:
                        items_details.append(self.item_details_to_html(item_details))
                    else:
                        items_details.append(self.item_details_to_string(item_details))
                cnt += 1
                if not cnt % 10:
                    self.save_db()
        else:
            print("No new ads to look for")
        self.save_db()
        self.items_links = []
        return items_details

    def load_db(self):
        if os.path.isfile(self.db_path):  # if the db's json exists, load it
            with open(self.db_path, "r") as db_file:
                self.db = json.load(db_file)
        else:  # if it doesn't exist, create a raw one and save it
            self.db = {
                "columns": [
                    "url",
                    "state",
                    "published",
                    "price",
                    "bedrooms",
                    "surface",
                    "address",
                    "furnished",
                    "images",
                    "description",
                ],
                "data": [],
            }
            self.save_db()

    def save_db(self):
        with open(self.db_path, "w") as db_file:
            json.dump(self.db, db_file)

    def upgrade_db(self):
        pass