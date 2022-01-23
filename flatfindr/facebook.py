# facebook marketplace
from email.policy import default
import os
import random
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from collections import defaultdict

from flatfindr.logins import LOGINS
from flatfindr.utils import KEYWORDS


class Facebook:
    def __init__(
        self,
        email=LOGINS["facebook"]["id"],
        password=LOGINS["facebook"]["pass"],
        path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "raw_data"
        ),
    ):
        self.email = email
        self.password = password
        self.path = path

        # Handle the 'Allow notifications box':
        option = Options()
        option.add_argument("--disable-infobars")
        option.add_argument("start-maximized")
        option.add_argument("--disable-extensions")
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

        self.main_url = "https://www.facebook.com"
        self.items_links = []
        self.db = {  # TODO: importer db depuis un json
            "url": [],
            "published": [],
            "price": [],
            "address": [],
            "surface": [],
            "bedrooms": [],
            "furnished": [],
            "description": [],
            "image": [],
        }

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
        except Exception:
            print(
                "Some exception occurred while trying to find username or password field"
            )

    def quit(self):
        self.driver.quit()

    def scrape_items_links(
        self, min_price=1_200, max_price=1_750, min_bedrooms=2, scroll=10
    ):
        url1 = "/marketplace/montreal/propertyrentals?"
        url2 = f"minPrice={min_price}&maxPrice={max_price}"
        url3 = f"&minBedrooms={min_bedrooms}"
        url4 = "&exact=false&latitude=45.5254&longitude=-73.5724&radius=2"
        self.driver.get(self.main_url + url1 + url2 + url3 + url4)

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
            item_url = item.get_attribute("href")
            if "/marketplace/item/" in item_url:
                item_url = item_url[: item_url.find("?")]
                # If this item has never been scraped before, we add it
                if item_url not in self.db["url"]:
                    self.items_links.append(item_url)

        return self.items_links

    def scrape_item_details(self, item_url):
        item_db = {}
        item_db["url"] = item_url

        self.driver.get(item_url)
        # Click on 'see more' button to have the full description
        buttons = self.driver.find_elements_by_xpath("//div[@role='button']")
        _ = [button.click() for button in buttons if button.text == "Voir plus"]
        sleep(random.uniform(0.2, 0.5))

        details = self.driver.find_elements_by_xpath("//span[@dir]")
        for i in range(len(details)):
            detail = details[i].text
            if not item_db.get("published") and KEYWORDS["published"] in detail:
                if KEYWORDS["day"] in detail:  # if published less than a week ago
                    item_db["published"] = int(detail[20])
                else:
                    # if published more than a week ago, we use 8 as default
                    item_db["published"] = 8
            if not item_db.get("price") and KEYWORDS["price"] in detail:
                item_db["price"] = int(detail[:5].replace(" ", ""))
            elif not item_db.get("address") and KEYWORDS["address"] in detail:
                item_db["address"] = detail.replace("Montréal, QC", "").replace(
                    ", ", ""
                )
            elif not item_db.get("surface") and KEYWORDS["surface(m2)"] in detail:
                surface = int(detail[:4].replace(" ", ""))
                # if the seller indicated square meters but is actually square feet
                if surface > 200:
                    surface = round(surface / 10.764)
                item_db["surface"] = surface
            elif not item_db.get("surface") and KEYWORDS["surface(ft2)"] in detail:
                item_db["surface"] = round(int(detail[:4].replace(" ", "")) / 10.764)
            elif not item_db.get("bedrooms") and KEYWORDS["bedrooms"] in detail:
                item_db["bedrooms"] = int(detail[0])
            elif not item_db.get("furnished") and detail in KEYWORDS["furnished"]:
                item_db["furnished"] = detail
            elif not item_db.get("description") and detail == KEYWORDS["description"]:
                item_db["description"] = details[i + 1].text.replace("Voir moins", "")

        item_db["image"] = set()
        try:
            img_cnt = -1
            while len(item_db["image"]) != img_cnt:
                img_cnt = len(item_db["image"])
                img = self.driver.find_element_by_xpath(
                    "//img[@referrerpolicy='origin-when-cross-origin']"
                )
                item_db["image"].add(img.get_attribute("src"))
                next_button = self.driver.find_element_by_xpath(
                    "//div[@aria-label='Voir l’image suivante']"
                )
                next_button.click()
                sleep(random.uniform(0.6, 1))
        except:
            pass

        for key, value in item_db.items():
            if key != "image":
                print(key + ":", value)
        print("\n  " + "=" * 40 + "\n  " + "=" * 40 + "\n")

        return item_db

    def scrape_items_details(self):
        if len(self.items_links):
            for item_url in self.items_links[:5]:
                item_db = self.scrape_item_details(item_url)
                for key in self.db:
                    self.db[key].append(item_db.get(key, ""))
        else:
            print("You should first scrape items links")
        return self.db


if __name__ == "__main__":
    fb = Facebook()
    fb.log_in()
    fb.scrape_items_links(scroll=0)
    fb.scrape_items_details()
    for key, value in fb.db.items():
        if key not in ("image", "description"):
            print(f"-> {key}: ")
            for v in value:
                print(v)
            print()
    # fb.quit()

