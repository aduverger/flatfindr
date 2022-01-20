# facebook marketplace
import os
import random
from collections import defaultdict
from io import BytesIO
from time import sleep

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from flatfindr.logins import LOGINS


class Facebook:
    def __init__(
        self,
        email=LOGINS["facebook"][0],
        password=LOGINS["facebook"][1],
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
            options=option, executable_path="/Users/aduverger/Downloads/chromedriver",
        )

        self.main_url = "https://www.facebook.com"
        self.item_links = []

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

    def scrape_item_links(
        self, db=defaultdict(list), min_price=1_200, max_price=1_750, min_bedrooms=2
    ):
        url1 = "/marketplace/montreal/propertyrentals?"
        url2 = f"minPrice={min_price}&maxPrice={max_price}"
        url3 = f"&minBedrooms={min_bedrooms}"
        url4 = "&exact=false&latitude=45.5254&longitude=-73.5724&radius=2"
        self.driver.get(self.main_url + url1 + url2 + url3 + url4)

        for i in range(10):
            try:
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                sleep(random.uniform(1, 1.5))
            except:
                pass

        all_href = self.driver.find_elements_by_xpath("//a[@href]")
        for item in all_href:
            item_url = item.get_attribute("href")
            if "/marketplace/item/" in item_url:
                item_url = item_url[: item_url.find("?")]
                if item_url not in db["url"]:
                    self.item_links.append(item_url)

        return self.item_links

    def scrape_item_details(self, item_url, db=defaultdict(list)):
        db["url"].append(item_url)

        fb.driver.get(item_url)
        # Click on 'see more' button to have the full description
        buttons = fb.driver.find_elements_by_xpath("//div[@role='button']")
        _ = [button.click() for button in buttons if button.text == "Voir plus"]
        sleep(random.uniform(0.2, 0.5))

        details = fb.driver.find_elements_by_xpath("//span[@dir]")
        price, adress, surface, bedrooms, description = [True] * 5
        for i in range(len(details)):
            detail = details[i].text
            if price and "$ / mois" in detail:
                db["price($/month)"].append(int(detail[:5].replace(" ", "")))
                price = False
            elif adress and "Montréal, QC" in detail:
                db["adress"].append(detail.replace("Montréal, QC", ""))
                adress = False
            elif surface and "mètres carrés" in detail:
                db["surface(m2)"].append(int(detail[:4].replace(" ", "")))
                surface = False
            elif surface and "pieds carrés" in detail:
                db["surface(m2)"].append(
                    round(int(detail[:4].replace(" ", "")) / 10.764)
                )
                surface = False
            elif bedrooms and "chambres · " in detail:
                db["bedrooms"].append(int(detail[0]))
                bedrooms = False
            elif detail in ("Meublé", "Non meublé"):
                db["furnished"].append(detail)
            elif description and detail == "Description":
                db["description"].append(details[i + 1].text.replace("Voir moins", ""))
                description = False

        img = fb.driver.find_element_by_xpath(
            "//img[@referrerpolicy='origin-when-cross-origin']"
        )
        db["image"].append(img.get_attribute("src"))

        for key, value in db.items():
            if key != "image":
                print(key + ":", value[-1])
            else:
                response = requests.get(db["image"][-1])
                Image.open(BytesIO(response.content)).resize((400, 400)).show()

        return db
        # try:
        #     previous_and_next_buttons = self.driver.find_elements_by_xpath(
        #         "//i[contains(@class, '_3ffr')]"
        #     )
        #     next_image_button = previous_and_next_buttons[1]
        #     while next_image_button.is_displayed():
        #         next_image_button.click()
        #         image_element = self.driver.find_element_by_xpath(
        #             '//img[contains(@class, "_5m")]'
        #         )
        #         sleep(1)
        #         if image_element.get_attribute("src") in images:
        #             break
        #         else:
        #             images.append(image_element.get_attribute("src"))
        # except:
        #     pass


if __name__ == "__main__":
    fb = Facebook()
    fb.log_in()
    fb.scrape_item_links()
    fb.scrape_item_details(item_url=fb.item_links[0])
    fb.quit()

