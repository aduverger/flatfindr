# facebook marketplace
import json
import os
import random
from datetime import date, timedelta
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from flatfindr.logins import LOGINS
from flatfindr.utils import KEYWORDS


class Facebook:
    def __init__(
        self,
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
        self.load_db()

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

        seen_links = [item_data[0] for item_data in self.db["data"]]

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
                    if item_url not in seen_links:
                        self.items_links.append(item_url)
            except:
                pass

        return self.items_links

    def scrape_item_details(self, item_url):
        item_data = {}
        item_data["url"] = item_url
        item_data["state"] = "new"

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
                if KEYWORDS["day"] in detail:  # if published less than a week ago
                    item_data["published"] = int(detail[20])
                elif KEYWORDS["week"] in detail:
                    # if published more than a week ago, we use 8 as default
                    item_data["published"] = 8
                else:
                    # if published less than a day ago, we use 0 as default
                    item_data["published"] = 0
                # Now let's transform this into a date
                item_data["published"] = (
                    date.today() - timedelta(days=item_data["published"])
                ).isoformat()
            if not item_data.get("price") and KEYWORDS["price"] in detail:
                try:
                    item_data["price"] = int(detail[:5].replace(" ", ""))
                except:
                    pass
            elif not item_data.get("address") and KEYWORDS["address"] in detail:
                item_data["address"] = detail.replace(KEYWORDS["montreal"], "").replace(
                    ", ", ""
                )
            elif not item_data.get("surface") and KEYWORDS["surface(m2)"] in detail:
                try:
                    surface = int(detail[:4].replace(" ", ""))
                    # if the seller indicated square meters but is actually square feet
                    if surface > 200:
                        surface = round(surface / 10.764)
                    item_data["surface"] = surface
                except:
                    pass
            elif not item_data.get("surface") and KEYWORDS["surface(ft2)"] in detail:
                try:
                    item_data["surface"] = round(
                        int(detail[:4].replace(" ", "")) / 10.764
                    )
                except:
                    pass
            elif not item_data.get("bedrooms") and KEYWORDS["bedrooms"] in detail:
                try:
                    item_data["bedrooms"] = int(detail[0])
                except:
                    pass
            elif not item_data.get("furnished") and detail in KEYWORDS["furnished"]:
                item_data["furnished"] = detail
            elif not item_data.get("description") and detail == KEYWORDS["description"]:
                item_data["description"] = details[i + 1].text.replace(
                    KEYWORDS["see_less"], ""
                )

        item_data["images"] = []
        try:
            while True:
                img = self.driver.find_element_by_xpath(
                    "//img[@referrerpolicy='origin-when-cross-origin']"
                )
                img_url = img.get_attribute("src")
                next_button = self.driver.find_element_by_xpath(
                    "//div[@aria-label='Voir l’image suivante']"
                )
                if any(size in img_url for size in ("p100x100", "p261x260")):
                    # If not a picture of the apartment
                    next_button.click()
                elif img_url not in item_data["images"]:
                    item_data["images"].append(img_url)
                    next_button.click()
                else:
                    break
                sleep(random.uniform(0.6, 1))
        except:
            pass

        for key, value in item_data.items():
            if key != "images":
                print(key + ":", value)
        print("\n  " + "=" * 40 + "\n  " + "=" * 40 + "\n")

        return item_data

    def scrape_items_details(self):
        if len(self.items_links):
            for item_url in self.items_links:
                item_data = self.scrape_item_details(item_url)
                self.db["data"].append(
                    [item_data.get(feature, "") for feature in self.db["columns"]]
                )
        else:
            print("You should first scrape items links")
        return self.db

    def load_db(self):
        if os.path.isfile(self.db_path):  # if the db's json exists, load it
            with open(self.db_path, "r") as db_file:
                self.db = json.load(db_file)
        else:  # if it doesn't exist, create a ra and save it
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


if __name__ == "__main__":
    fb = Facebook()
    fb.log_in()
    fb.scrape_items_links(scroll=100)
    # fb.scrape_item_details(
    #     "https://www.facebook.com/marketplace/item/4430069320431045/"
    # )
    fb.scrape_items_details()
    fb.save_db()
    fb.quit()

