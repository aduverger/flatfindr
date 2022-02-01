# facebook marketplace
import json
import os
import random
import pickle
from datetime import date, timedelta
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from flatfindr.logins import LOGINS
from flatfindr.utils import KEYWORDS

ONE_WEEK = 8
MAX_ITEMS = 30


class Facebook:
    def __init__(
        self,
        headless=False,
        email=LOGINS["facebook"]["id"],
        password=LOGINS["facebook"]["pass"],
        db_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "raw_data/db.json",
        ),
    ):
        self.email = email
        self.password = password
        self.db_path = db_path
        self.load_driver(headless=headless)
        self.main_url = "https://www.facebook.com"
        self.items_links = []
        self.load_db()

    def load_driver(self, headless=False):
        # Handle the 'Allow notifications box':
        option = Options()
        option.add_argument("--disable-infobars")
        option.add_argument("start-maximized")
        option.add_argument("--disable-extensions")
        if headless:
            option.add_argument("--headless")
        # Pass the argument 1 to allow and 2 to block
        option.add_experimental_option(
            "prefs", {"profile.default_content_setting_values.notifications": 2}
        )
        self.driver = webdriver.Chrome(
            options=option,
            executable_path=os.path.join(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                "chromedriver",
            ),
        )

    def quit_driver(self):
        self.driver.quit()

    def log_in(self):
        self.driver.get(self.main_url)
        try:
            email_input = self.driver.find_element_by_id("email")
            email_input.send_keys(self.email)
            sleep(random.uniform(0.2, 0.5))
            password_input = self.driver.find_element_by_id("pass")
            password_input.send_keys(self.password)
            sleep(random.uniform(0.2, 0.5))
            login_button = self.driver.find_element_by_xpath("//*[@type='submit']")
            login_button.click()
            sleep(random.uniform(2, 3))
            self.save_cookies()
        except Exception:
            print(
                "Some exception occurred while trying to find username or password field"
            )

    def save_cookies(self):
        cookies_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "raw_data/cookies.pkl",
        )
        with open(cookies_path, "wb") as cookies_file:
            pickle.dump(self.driver.get_cookies(), cookies_file)

    def load_cookies(self):
        self.driver.get(self.main_url)
        cookies_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "raw_data/cookies.pkl",
        )
        with open(cookies_path, "rb") as cookies_file:
            cookies = pickle.load(cookies_file)
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    def get_items_links(
        self,
        min_price=1_200,
        max_price=1_750,
        min_bedrooms=2,
        lat=45.5254,
        lng=-73.5724,
        radius=2,
        scroll=10,
    ):
        rentals = "/marketplace/montreal/propertyrentals?"
        price = f"minPrice={min_price}&maxPrice={max_price}"
        bedrooms = f"&minBedrooms={min_bedrooms}"
        pos = f"&exact=false&latitude={lat}&longitude={lng}&radius={radius}"
        self.driver.get(self.main_url + rentals + price + bedrooms + pos)

        seen_links = [data[0] for data in self.db["data"]]

        for _ in range(scroll):
            try:
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                sleep(random.uniform(0.8, 1.2))
            except:
                pass

        all_href = self.driver.find_elements_by_xpath("//a[@href]")
        for item in all_href:
            try:
                item_url = item.get_attribute("href")
                if "/marketplace/item/" in item_url:
                    item_url = item_url[: item_url.find("?")]
                    # If this item has never been scraped before, we add it
                    if item_url not in seen_links and item_url not in self.items_links:
                        self.items_links.append(item_url)
            except:
                pass

        return self.items_links

    def get_item_publication_day(self, detail):
        if KEYWORDS["day"] in detail:  # if published less than a week ago
            try:
                publication_day = int(detail[20])
            except:
                print("Error while casting publication day")
                return 0
        elif KEYWORDS["week"] in detail:
            # if published more than a week ago, we use 8 as default
            publication_day = ONE_WEEK
        else:
            # if published less than a day ago, we use 0 as default
            publication_day = 0
        # Transform into a date
        return (date.today() - timedelta(days=publication_day)).isoformat()

    def get_item_price(self, detail):
        try:
            return int(detail[:5].replace(" ", ""))
        except:
            print("Error while casting price")
            return 0

    def get_item_address(self, detail):
        return detail.replace(KEYWORDS["montreal"], "").replace(", ", "")

    def get_item_surface(self, detail):
        try:
            surface = int(detail[:4].replace(" ", ""))
        except:
            print("Error while casting surface")
            return 0
        if KEYWORDS["surface(ft2)"] in detail or surface > 200:
            # if square feet (considering that a surface > 200 is necessarily in ft2)
            surface = round(surface / 10.764)
        return surface

    def get_item_bedrooms(self, detail):
        try:
            return int(detail[0])
        except:
            print("Error while casting number of bedrooms")
            return 0

    def get_item_description(self, detail):
        return detail.replace(KEYWORDS["see_less"], "")

    def get_item_images(self):
        images = []
        cnt = 0
        while cnt < 30:
            try:
                img = self.driver.find_element_by_xpath(
                    "//img[@referrerpolicy='origin-when-cross-origin']"
                )
                img_url = img.get_attribute("src")
                if any(size in img_url for size in ("p720x720", "s960x960")):
                    # If a picture of the apartment
                    if img_url not in images:  # if unseen
                        images.append(img_url)
                    else:
                        break  # if already seen
            except:
                print("Error while scraping images")
            cnt += 1
            try:
                next_button = self.driver.find_element_by_xpath(
                    f"//div[@aria-label='{KEYWORDS['next_img']}']"
                )
                next_button.click()
                sleep(random.uniform(0.6, 1))
            except:  # only 1 picture for this ad so there is no next button
                break
        return images

    def item_details_to_string(self, item_data):
        sentence = ""
        for key, value in item_data.items():
            if key not in ("images", "state"):
                sentence += f"{key}: {value} \n"
        sentence += "\n  " + "=" * 40 + "\n  " + "=" * 40 + "\n"
        return sentence

    def item_details_to_html(self, item_data):
        sentence = ""
        for key, value in item_data.items():
            if key not in ("images", "state"):
                if key == "url":
                    sentence += f"{key}: <a target='_blank' href='{value}'>{value[-15:-1]}</a> \n"
                elif key == "address":
                    href = f"""https://www.google.com/maps/place/{value.replace(" ", "+").replace("'", "+")},+Montr%C3%A9al,+QC"""
                    sentence += (
                        f"{key}: <a target='_blank' href='{href}'>{value}</a> \n"
                    )
                elif key == "price":
                    sentence += f"{key}: {value} € \n"
                elif key == "surface":
                    sentence += f"{key}: {value} m² \n"
                else:
                    sentence += f"{key}: {value} \n"
        return sentence

    def is_old(self, item_data):
        return (
            item_data.get("published")
            == (date.today() - timedelta(days=ONE_WEEK)).isoformat()
        )

    def is_duplicate(self, item_data):
        all_description = [data[-1] for data in self.db["data"] if data[-1] != ""]
        return item_data.get("description") in all_description

    def is_swap(self, item_data):
        return any(
            swap in item_data.get("description", "").lower()
            for swap in ("swap", "transfer", "échange", "exchange")
        )

    def is_first_floor(self, item_data):
        return any(
            ff in item_data.get("description", "").lower()
            for ff in (
                "ground floor",
                "first floor",
                "rdc",
                "rez-de-chaussée",
                "rez de chaussée",
            )
        )

    def get_item_details(self, item_url, remove_swap=True, remove_first_floor=True):
        item_data = {}
        item_data["url"] = item_url
        self.driver.get(item_url)
        # Click on 'see more' button to get the full description
        buttons = self.driver.find_elements_by_xpath("//div[@role='button']")
        _ = [
            button.click() for button in buttons if button.text == KEYWORDS["see_more"]
        ]
        sleep(random.uniform(0.2, 0.5))

        details = self.driver.find_elements_by_xpath("//span[@dir]")
        for i in range(len(details)):
            detail = details[i].text
            if not item_data.get("published") and KEYWORDS["published"] in detail:
                item_data["published"] = self.get_item_publication_day(detail)
            elif not item_data.get("price") and KEYWORDS["price"] in detail:
                item_data["price"] = self.get_item_price(detail)
            elif not item_data.get("address") and KEYWORDS["address"] in detail:
                item_data["address"] = self.get_item_address(detail)
            elif not item_data.get("surface") and (
                KEYWORDS["surface(m2)"] in detail or KEYWORDS["surface(ft2)"] in detail
            ):
                item_data["surface"] = self.get_item_surface(detail)
            elif not item_data.get("bedrooms") and KEYWORDS["bedrooms"] in detail:
                item_data["bedrooms"] = self.get_item_bedrooms(detail)
            elif not item_data.get("furnished") and detail in KEYWORDS["furnished"]:
                item_data["furnished"] = detail
            elif not item_data.get("description") and detail == KEYWORDS["description"]:
                detail = details[i + 1].text
                item_data["description"] = self.get_item_description(detail)

        if any(
            (
                self.is_old(item_data),
                self.is_duplicate(item_data),
                self.is_swap(item_data) and remove_swap,
                self.is_first_floor(item_data) and remove_first_floor,
            )
        ):
            # We are not interested by this ads
            item_data["state"] = "NI"
            item_data["description"] = ""
            item_data["images"] = []
        else:
            item_data["state"] = "new"
            item_data["images"] = self.get_item_images()
            print(self.item_details_to_string(item_data))
        return item_data

    def get_items_details(self, for_alfred=False):
        items_details_strings = []
        if len(self.items_links):
            cnt = 0
            for item_url in self.items_links[:MAX_ITEMS]:
                item_data = self.get_item_details(item_url)
                self.db["data"].append(
                    [item_data.get(feature, "") for feature in self.db["columns"]]
                )
                if item_data.get("state") == "new":
                    # If the ad is interesting, we add its string description for the bot to display
                    if for_alfred:
                        items_details_strings.append(
                            self.item_details_to_html(item_data)
                        )
                    else:
                        items_details_strings.append(
                            self.item_details_to_string(item_data)
                        )
                cnt += 1
                if not cnt % 10:
                    self.save_db()
        else:
            print("No new ads to look for")

        self.save_db()
        self.items_links = []
        return items_details_strings

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


if __name__ == "__main__":
    fb = Facebook()
    cookies_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "raw_data/cookies.pkl",
    )
    if not os.path.isfile(cookies_path):
        fb.log_in()
    else:
        fb.load_cookies()

    fb.get_items_links(
        min_price=1_200,
        max_price=1_750,
        min_bedrooms=2,
        lat=45.5254,
        lng=-73.5724,
        radius=2,
        scroll=15,
    )
    # fb.get_item_details("https://www.facebook.com/marketplace/item/255094690033809/")
    fb.get_items_details()

    fb.save_db()
    fb.quit_driver()

