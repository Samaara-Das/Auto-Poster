# import modules
from time import sleep, time
from database_manager import DatabaseManager
from logger import logger, clear_log_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from os import getenv
from dotenv import load_dotenv
from delete_reactions import delete_all_replies, delete_all_likes
import json

# Load environment variables
load_dotenv()

# Replace the hardcoded values with environment variables
CHROMEDRIVER_EXE_PATH = getenv('CHROMEDRIVER_EXE_PATH')
CHROME_PROFILES_PATH = getenv('CHROME_PROFILES_PATH')

class Browser:

    def __init__(self, keep_open: bool) -> None:
        clear_log_file()
        chrome_options = Options() 
        chrome_options.add_experimental_option("detach", keep_open)
        chrome_options.add_argument('--profile-directory=Profile 12') # This profile is for the policy vote account
        chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILES_PATH}")
        self.driver = webdriver.Chrome(service=ChromeService(executable_path=CHROMEDRIVER_EXE_PATH), options=chrome_options)
        self.logger = logger(__name__)
        self.keep_open = keep_open  # Store the keep_open flag
        self.processed_profiles = set() # Always return an empty set when the program starts

    def save_processed_profiles(self):
        with open('processed_profiles.json', 'w') as f:
            json.dump(list(self.processed_profiles), f)

    def is_profile_processed(self, profile_url):
        return profile_url in self.processed_profiles

    def mark_profile_as_processed(self, profile_url):
        self.processed_profiles.add(profile_url)
        self.save_processed_profiles()

    def open_page(self, url: str):
        '''This opens `url` and maximizes the window'''
        try:
            self.driver.get(url)
            self.driver.set_window_size(1920, 1080)  # Set a large default size
            self.driver.maximize_window()
            # Double-check and force maximize if needed
            if self.driver.get_window_size()['width'] < 1920:
                self.driver.fullscreen_window()
            self.logger.info(f'Opened this url: {url}')
            return True
        except WebDriverException:
            self.logger.exception(f'Cannot open this url: {url}. Error: ')
            return False 
        
    def go_to_following(self, username: str):
        self.driver.get(f'https://x.com/{username}/following')

    def open_profile_in_new_tab(self):
        """
        This method finds the next unprocessed profile link in the "Following" timeline,
        extracts its URL, and opens it in a new tab. It returns True if successful,
        False if no more profiles to process, and logs the outcome.
        """
        try:
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Find the timeline element
            timeline_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Timeline: Following"]'))
            )

            # Find all profile links
            profile_links = timeline_div.find_elements(By.XPATH, './/div[contains(@class, "css-175oi2r r-1wbh5a2 r-dnmrzs")]//a')

            for link in profile_links:
                href = link.get_attribute('href')
                if not self.is_profile_processed(href):
                    self.driver.execute_script(f"window.open('{href}', '_blank');")
                    self.logger.info(f'Opened profile in new tab: {href}')
                    self.mark_profile_as_processed(href)
                    return True

            # If we've gone through all visible links, try scrolling
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                self.logger.info("No more profiles to process")
                return False  # No more profiles to process

            return self.open_profile_in_new_tab()  # Recursively call after scrolling

        except Exception as e:
            self.logger.exception(f'Failed to open profile in new tab. Error: {str(e)}')
            return False

    def scroll_to_latest_post(self):
        """
        Scrolls down to the latest non-ad and non-pinned post on an X profile.
        Returns the tweet element if found, None otherwise.
        """
        try:
            # Wait for the timeline to be present
            timeline = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@aria-label, "Timeline")]'))
            )

            # Scroll until a non-ad and non-pinned tweet article is visible or max attempts reached
            max_attempts = 20
            for _ in range(max_attempts):
                tweets = timeline.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
                for tweet in tweets:
                    # Check if the tweet is an ad or pinned
                    ad_span = tweet.find_elements(By.XPATH, './/span[text()="Ad"]')
                    pinned_div = tweet.find_elements(By.XPATH, './/div[text()="Pinned"]')
                    if not ad_span and not pinned_div:
                        # Scroll the tweet into view using JavaScript
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", tweet)
                        sleep(1)  # Wait for the scroll to complete
                        self.logger.info("Successfully scrolled to the latest non-ad and non-pinned post")
                        return tweet
                
                # If no suitable tweet found, scroll down
                self.driver.execute_script("window.scrollBy(0, 500);")
                sleep(1)  # Wait for content to load
            
            self.logger.warning("Couldn't find a non-ad and non-pinned tweet after maximum scroll attempts")
            return None
        except Exception as e:
            self.logger.exception(f"Failed to scroll to latest non-ad and non-pinned post. Error: {str(e)}")
            return None

    def expand_latest_tweet(self):
        """
        Expands the latest tweet if it has a "Show more" link.
        Returns the tweet element if expanded, None otherwise.
        """
        try:
            tweet = self.scroll_to_latest_post()
            if not tweet:
                return None

            # Check if there's a "Show more" link
            show_more = tweet.find_elements(By.XPATH, './/div[@data-testid="tweet-text-show-more-link"]')
            if show_more:
                show_more[0].click()
                sleep(1)  # Short wait for content to expand
                self.logger.info("Successfully expanded the latest tweet")
            else:
                self.logger.info("No 'Show more' link found, tweet is already fully visible")

            return tweet
        except Exception as e:
            self.logger.exception(f"Failed to expand latest tweet. Error: {str(e)}")
            return None

    def get_tweet_link(self, tweet_element):
        """
        Extracts the tweet link from the given tweet element.
        """
        try:
            link_element = tweet_element.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
            return link_element.get_attribute('href')
        except NoSuchElementException:
            self.logger.error("Could not find tweet link")
            return None

    def get_tweet_author(self, tweet_element):
        """
        Extracts the username of the tweet author from the given tweet element.
        """
        try:
            author_element = tweet_element.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span[contains(text(), "@")]')
            return author_element.text.strip('@')
        except NoSuchElementException:
            self.logger.error("Could not find tweet author")
            return None

    def like_tweet(self, tweet_element):
        """
        Checks if the given tweet is liked. If not, it likes the tweet.
        Returns True if the tweet is (or was successfully) liked, False otherwise.
        """
        try:
            # Find the like/unlike button within the tweet element
            like_button = tweet_element.find_element(By.XPATH, './/button[@data-testid="like" or @data-testid="unlike"]')
            
            # Check if the tweet is already liked
            if like_button.get_attribute('data-testid') == 'unlike':
                self.logger.info("Tweet is already liked")
                return True
            
            # If not liked, click the like button
            like_button.click()
            sleep(1)  # Wait for the like action to complete
            
            self.logger.info("Successfully liked the tweet")
            return True
        except NoSuchElementException:
            self.logger.error("Could not find the like/unlike button")
            return False
        except Exception as e:
            self.logger.exception(f"Failed to like the tweet. Error: {str(e)}")
            return False

    def click_reply_button(self, tweet_element):
        """
        Clicks the reply button of the given tweet.
        Returns True if the reply button was successfully clicked, False otherwise.
        """
        try:
            # Find the reply button within the tweet element
            reply_button = tweet_element.find_element(By.XPATH, './/button[@data-testid="reply"]')
            
            # Click the reply button
            reply_button.click()
            sleep(1)  # Wait for the reply dialog to open
            
            self.logger.info("Successfully clicked the reply button")
            return True
        except NoSuchElementException:
            self.logger.error("Could not find the reply button")
            return False
        except Exception as e:
            self.logger.exception(f"Failed to click the reply button. Error: {str(e)}")
            return False

    def type_reply(self, reply_text):
        """
        Types the given text into the reply box.
        """
        try:
            reply_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="tweetTextarea_0"]'))
            )
            reply_box.send_keys(reply_text)
            self.logger.info(f"Successfully typed reply: {reply_text}")
            return True
        except Exception as e:
            self.logger.exception(f"Failed to type reply. Error: {str(e)}")
            return False

    def send_reply(self):
        """
        Clicks the send button for the reply.
        """
        try:
            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="tweetButton"]'))
            )
            send_button.click()
            sleep(2)  # Wait for the reply to be sent
            self.logger.info("Successfully clicked the reply send button")
            return True
        except TimeoutException:
            self.logger.exception(f"Failed to click reply send button. Error: TimeoutException")
            return False
        except Exception as e:
            self.logger.exception(f"Failed to click reply send button. Error: {str(e)}")
            return False

    def close_current_tab(self):
        """
        Closes the current tab and switches back to the previous one.
        """
        try:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.logger.info("Closed the current tab and switched back to the previous one")
            return True
        except Exception as e:
            self.logger.exception(f"Failed to close tab. Error: {str(e)}")
            return False

if __name__ == '__main__':
    # Clear the processed_profiles.json file before starting so that there's no record of previously processed profiles and the program starts with a clean slate.
    with open('processed_profiles.json', 'w') as f:
        json.dump([], f)
    
    db_manager = DatabaseManager()
    browser = Browser(keep_open=True)

    username = getenv('USERNAME')
    browser.go_to_following(username)

    max_retries = 3
    retry_delay = 5  # seconds
    profile_delay = 2  # seconds between processing profiles

    while True:
        try:
            if not browser.open_profile_in_new_tab():
                break  # No more profiles to process

            browser.driver.switch_to.window(browser.driver.window_handles[-1])
            
            tweet_element = browser.scroll_to_latest_post()
            if tweet_element:
                tweet_link = browser.get_tweet_link(tweet_element)
                tweet_author = browser.get_tweet_author(tweet_element)
                if tweet_link and tweet_author:
                    db_manager.save_tweet(tweet_link, tweet_author)
                    print(f"Saved tweet link: {tweet_link} by author: {tweet_author}")
                    
                    # Like the tweet
                    for attempt in range(max_retries):
                        if browser.like_tweet(tweet_element):
                            print(f"Liked the tweet by {tweet_author} successfully")
                            
                            # Send a reply
                            if browser.click_reply_button(tweet_element):
                                reply_text = f"Great tweet, @{tweet_author}! Thanks for sharing."
                                if browser.type_reply(reply_text) and browser.send_reply():
                                    print(f"Replied to the tweet by {tweet_author} successfully")
                                else:
                                    print(f"Failed to send reply to {tweet_author}")
                            else:
                                print(f"Failed to open reply dialog for {tweet_author}")
                            
                            break
                        else:
                            if attempt < max_retries - 1:
                                print(f"Failed to like tweet, retrying in {retry_delay} seconds...")
                                sleep(retry_delay)
                            else:
                                print(f"Failed to like the tweet by {tweet_author} after {max_retries} attempts")
                else:
                    print(f"Failed to get tweet link for {tweet_author}")
            else:
                print("Failed to find the latest non-ad and non-pinned tweet")
            
            # Close the current tab and switch back to the following list
            browser.close_current_tab()
            
            # Add a delay to avoid rate limiting
            sleep(profile_delay)

        except Exception as e:
            print(f"An error occurred while processing a profile: {str(e)}")
            browser.logger.exception("Error in main loop")
            # Attempt to close the current tab and continue with the next profile
            try:
                browser.close_current_tab()
            except:
                pass
            sleep(retry_delay)
            continue

    if browser.keep_open:
        input("Press Enter to close the browser...")  # Wait for user input before closing

