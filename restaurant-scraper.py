from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import pandas as pd
import re

class RestaurantScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def scrape_restaurants(self, url):
        self.driver.get(url)
        feed = self.scroll_to_end()
        restaurants_data = []
	
        try:
            feed = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
            time.sleep(3)
            
            try:
                restaurant_links = feed.find_elements(By.CSS_SELECTOR, ':scope > div > div > a')
                
                for index, link in enumerate(restaurant_links):
                    print(f"Processing item #{index + 1} out of {len(restaurant_links)}")
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView();", link)
                        time.sleep(0.5)
                        
                        link.click()
                        time.sleep(2)
                        
                        print("Extracting restaurant information")
                        restaurant_info = self.extract_restaurant_info()
                        if restaurant_info:
                            restaurants_data.append(restaurant_info)
                            print(f"Scraped: {restaurant_info['name']}")
                        
                    except Exception as e:
                        print(f"Error processing restaurant: {str(e)}")
                        continue
                
            except Exception as e:
                print(f"Error processing page: {str(e)}")
                
        except Exception as e:
            print(f"Error finding feed: {str(e)}")
            
        return restaurants_data
    
    def scroll_to_end(self):
        try:
            feed = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
            time.sleep(3)
            
            print("Scrolling to load all restaurants...")
            last_height = self.driver.execute_script("return document.querySelector('div[role=\"feed\"]').scrollHeight")
            scroll_attempts = 0
            max_attempts = 50
            
            while scroll_attempts < max_attempts:
                self.driver.execute_script("""
                    var feed = document.querySelector('div[role="feed"]');
                    feed.scrollTo(0, feed.scrollHeight * 2);
            		""")
                time.sleep(2)
            
                try:
                    end_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'reached the end of the list')]")
                    if end_text.is_displayed():
                        print("Reached the end of the list")
                        return feed
                except:
                    pass
            
                new_height = self.driver.execute_script("return document.querySelector('div[role=\"feed\"]').scrollHeight")
                
                if new_height == last_height:
                    time.sleep(2)
                    new_height = self.driver.execute_script("return document.querySelector('div[role=\"feed\"]').scrollHeight")
                    if new_height == last_height:
                        print("No more results to load")
                        return feed
                
                last_height = new_height
                scroll_attempts += 1
                
                if scroll_attempts % 5 == 0:
                    print(f"Scrolled {scroll_attempts} times...")
            
            print("Reached maximum scroll attempts")
            return feed
            
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")
            return None
    
    def extract_restaurant_info(self):
        try:
            main_divs = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="main"]')))
            main_div = main_divs[1]
            
            name = main_div.find_element(By.CSS_SELECTOR, 'h1, h2').text
            
            phone = website = address = "N/A"
            
            address_buttons = main_div.find_elements(By.CSS_SELECTOR, 'button[data-item-id^="address"]')
            if address_buttons:
                address = address_buttons[0].text
                address = re.sub(r'[^\w\s,.-]', '', address)  # Remove special chars except comma, period, hyphen
                address = re.sub(r'\s+', ' ', address)        # Replace multiple spaces with single space
                address = address.strip()                     # Remove leading/trailing spaces
            
            phone_buttons = main_div.find_elements(By.CSS_SELECTOR, 'button[data-item-id^="phone"]')
            if phone_buttons:
                phone = phone_buttons[0].text
                phone_match = re.search(r'(?:\+\d{1,3}[\s.-]?)?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,4}', phone)
                if phone_match:
                    phone = phone_match.group(0)
                    # Remove all non-digit and non-plus characters
                    phone = re.sub(r'[^\d+]', ' ', phone)
                    # Remove extra spaces
                    phone = ' '.join(phone.split())
            
            website_buttons = main_div.find_elements(By.CSS_SELECTOR, 'a[data-item-id^="authority"]')
            if website_buttons:
                website = website_buttons[0].text
                website_match = re.search(r'(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+)', website)
                if website_match:
                    website = website_match.group(1)
                
            print(f"Name: {name}")
            print(f"Phone: {phone}")
            print(f"Website: {website}")
            print(f"Address: {address}")
            
            return {
                'name': name,
                'phone': phone,
                'website': website,
                'address': address
            }
            
        except Exception as e:
            print(f"Error extracting restaurant info: {str(e)}")
            return None
    
    def save_to_csv(self, data, filename='restaurants.csv'):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    
    def close(self):
        self.driver.quit()

def main():
    url = "https://www.google.com/maps/search/Restaurants/@-34.4248013,150.8874009,17z"
    
    scraper = RestaurantScraper()
    try:
        restaurants_data = scraper.scrape_restaurants(url)
        scraper.save_to_csv(restaurants_data)
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 