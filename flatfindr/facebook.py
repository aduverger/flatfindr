# facebook marketplace
import os
import random
from collections import defaultdict
from time import sleep

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
        print(path)

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

    def scrape_item_details(self, db, item_links):
        for url in item_links:
            images = []
            self.driver.get(url)
            sleep(0.5)

            url = url
            try:
                image_element = self.driver.find_element_by_xpath(
                    '//img[contains(@class, "_5m")]'
                )
                images = [image_element.get_attribute("src")]
            except:
                images = ""
            try:
                title = self.driver.find_element_by_xpath(
                    '//div[contains(@class, " _50f")]/span'
                ).text
            except:
                title = ""
            try:
                date_time = self.driver.find_element_by_xpath('//a[@class="_r3j"]').text
            except:
                date_time = ""
            try:
                location = self.driver.find_element_by_xpath(
                    '//span[@class="_7yi"]'
                ).text
            except:
                location = ""
            try:
                price = self.driver.find_element_by_xpath(
                    '//div[contains(@class, "_5_md")]'
                ).text
            except:
                price = ""
            try:
                if self.driver.find_element_by_xpath(
                    "//a[@title='More']"
                ).is_displayed():
                    self.driver.find_element_by_xpath("//a[@title='More']").click()
                description = self.driver.find_element_by_xpath(
                    '//p[@class="_4etw"]/span'
                ).text
            except:
                description = ""

            try:
                previous_and_next_buttons = self.driver.find_elements_by_xpath(
                    "//i[contains(@class, '_3ffr')]"
                )
                next_image_button = previous_and_next_buttons[1]
                while next_image_button.is_displayed():
                    next_image_button.click()
                    image_element = self.driver.find_element_by_xpath(
                        '//img[contains(@class, "_5m")]'
                    )
                    sleep(1)
                    if image_element.get_attribute("src") in images:
                        break
                    else:
                        images.append(image_element.get_attribute("src"))
            except:
                pass

        db.Facebook_items.insert(
            {
                "Url": url,
                "Images": images,
                "Title": title,
                "Description": description,
                "Date_Time": date_time,
                "Location": location,
                "Price": price,
            }
        )

        print(
            {
                "Url": url,
                "Images": images,
                "Title": title,
                "Description": description,
                "Date_Time": date_time,
                "Location": location,
                "Price": price,
            }
        )


if __name__ == "__main__":
    fb = Facebook()
    # fb.log_in()
    # fb.scrape_item_links()
    # # fb.scrape_item_details()
    # fb.quit()

