import os
import random
from datetime import date, timedelta
from time import sleep

from flatfindr.scraper import Scraper
from flatfindr.utils import KEYWORDS

ONE_WEEK = 8
""" 
An example subscraper class (heriting from Scraper) with all the method needed to be implemented to work properly within the flatfindr library
One new website to scrap == One new subscraper class (e.g. Facebook, Kijiji, etc.)
"""


class Subscraper(Scraper):
    def __init__(
        self,
        website="WEBSITE_NAME",
        headless=False,
        db_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            os.path.join("raw_data", "db.json"),
        ),
    ):
        super().__init__(website, headless=headless, db_path=db_path)

    def log_in(self):
        self.driver.get(self.main_url)
        try:
            # Implement here the code to log into the website
            pass
        except:
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
        self.driver.get(self.main_url + "")
        seen_links = [data[0] for data in self.db["data"]]

        all_href = []  # implement here the code to get items links
        for item in all_href:
            try:
                item_url = item.get_attribute("href")
                if item_url not in seen_links and item_url not in self.items_links:
                    # If this item has never been scraped before, we add it
                    self.items_links.append(item_url)
            except:
                pass

        return self.items_links

    def get_item_publication_day(self, detail):
        if KEYWORDS["day"] in detail:  # if published less than a week ago
            try:
                publication_day = int(detail)
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
            return int(detail.replace(" ", ""))
        except:
            print("Error while casting price")
            return 0

    def get_item_address(self, detail):
        return detail.replace(KEYWORDS["montreal"], "").replace(", ", "")

    def get_item_surface(self, detail):
        try:
            surface = int(detail.replace(" ", ""))
        except:
            print("Error while casting surface")
            return 0
        if KEYWORDS["surface(ft2)"] in detail or surface > 200:
            # if square feet (considering that a surface > 200 is necessarily in ft2)
            surface = round(surface / 10.764)
        return surface

    def get_item_bedrooms(self, detail):
        try:
            return int(detail)
        except:
            print("Error while casting number of bedrooms")
            return 0

    def get_item_description(self, detail):
        return detail.replace(KEYWORDS["see_less"], "")

    def get_item_images(self):
        images = []
        # implement here the code to get all images links and add them to `images`
        return images

    def get_item_details(self, item_url, remove_swap=True, remove_first_floor=True):
        item_details = super().get_item_details(item_url)
        details = []  # implement here the code to get details about the item
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
            item_details["images"] = self.get_item_images()
        return item_details
