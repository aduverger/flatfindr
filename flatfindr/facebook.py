# facebook marketplace
import os
import random
from datetime import date, timedelta
from time import sleep

from flatfindr.scraper import Scraper
from flatfindr.utils import KEYWORDS

ONE_WEEK = 8


class Facebook(Scraper):
    def __init__(
        self,
        headless=False,
        db_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            os.path.join("raw_data", "db.json"),
        ),
    ):
        super().__init__(
            website="facebook", headless=headless,db_path=db_path
        )

    def log_in(self):
        self.driver.get(self.main_url)
        sleep(random.uniform(2, 2.5))
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
            # self.save_cookies()
        except Exception:
            print(
                "Some exception occurred while trying to find username or password field"
            )

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
        sleep(random.uniform(5, 7)) # wait a bit so that the RasPi can load the page

        seen_links = [data[0] for data in self.db["data"]]

        for _ in range(scroll):
            try:
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                sleep(random.uniform(1.5, 2))
            except:
                pass

        sleep(random.uniform(2, 3)) # wait a bit so that the RasPi can load the page
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
                sleep(random.uniform(1, 1.2))
            except:  # only 1 picture for this ad so there is no next button
                break
        return images

    def get_item_details(self, item_url, remove_swap=True, remove_first_floor=True):
        item_details = super().get_item_details(item_url)
        sleep(random.uniform(5, 5.5)) # wait a bit so that the RasPi can load the page
        all_href = self.driver.find_elements_by_xpath("//a[@href]")

        # Click on 'see more' button to get the full description
        buttons = self.driver.find_elements_by_xpath("//div[@role='button']")
        _ = [
            button.click() for button in buttons if button.text == KEYWORDS["see_more"]
        ]
        sleep(random.uniform(0.5, 0.9))

        details = self.driver.find_elements_by_xpath("//span[@dir]")
        for i in range(len(details)):
            detail = details[i].text
            if not item_details.get("published") and KEYWORDS["published"] in detail:
                item_details["published"] = self.get_item_publication_day(detail)
            elif not item_details.get("price") and KEYWORDS["price"] in detail:
                item_details["price"] = self.get_item_price(detail)
            elif not item_details.get("address") and KEYWORDS["address"] in detail:
                item_details["address"] = self.get_item_address(detail)
            elif not item_details.get("surface") and (
                KEYWORDS["surface(m2)"] in detail or KEYWORDS["surface(ft2)"] in detail
            ):
                item_details["surface"] = self.get_item_surface(detail)
            elif not item_details.get("bedrooms") and KEYWORDS["bedrooms"] in detail:
                item_details["bedrooms"] = self.get_item_bedrooms(detail)
            elif not item_details.get("furnished") and detail in KEYWORDS["furnished"]:
                item_details["furnished"] = detail
            elif (
                not item_details.get("description")
                and detail == KEYWORDS["description"]
            ):
                detail = details[i + 1].text
                item_details["description"] = self.get_item_description(detail)

        if any(
            (
                self.is_old(item_details),
                self.is_duplicate(item_details),
                self.is_swap(item_details) and remove_swap,
                self.is_first_floor(item_details) and remove_first_floor,
            )
        ):
            # We are not interested by this ads
            item_details["state"] = "NI"
            item_details["description"] = ""
            item_details["images"] = []
        else:
            item_details["state"] = "new"
            item_details["images"] = [] # self.get_item_images()
        return item_details
