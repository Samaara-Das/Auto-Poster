# import modules
from time import sleep, time
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

CHROMEDRIVER_EXE_PATH = 'C:\\Users\\Puja\\Work\\Coding\\Python\\chromedriver.exe'
CHROME_PROFILES_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'

class Browser:

    def __init__(self, keep_open: bool) -> None:
        clear_log_file()
        chrome_options = Options() 
        chrome_options.add_experimental_option("detach", keep_open)
        chrome_options.add_argument('--profile-directory=Profile 11') # Use a fake profile so that X won't flag a real profile (mine or anyone else's)
        chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILES_PATH}")
        self.driver = webdriver.Chrome(service=ChromeService(executable_path=CHROMEDRIVER_EXE_PATH), options=chrome_options)
        self.logger = logger(__name__)
        self.keep_open = keep_open  # Store the keep_open flag

    def open_page(self, url: str):
        '''This opens `url` and maximizes the window'''
        try:
            self.driver.maximize_window()
            self.driver.get(url)
            self.logger.info(f'Opened this url: {url}')
            return True
        except WebDriverException:
            self.logger.exception(f'Cannot open this url: {url}. Error: ')
            return False 
        
    def go_to_following(self, username: str):
        self.driver.get(f'https://x.com/{username}/following')

    def open_profile_in_new_tab(self):
        """
        This method finds the first profile link in the "Following" timeline,
        extracts its URL, and opens it in a new tab. It returns True if successful,
        False otherwise, and logs the outcome.
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

            # Find the first profile link using the specific hierarchy
            profile_link = WebDriverWait(timeline_div, 5).until(
                EC.presence_of_element_located((By.XPATH, './/div[contains(@class, "css-175oi2r r-1wbh5a2 r-dnmrzs")]//a'))
            )

            href = profile_link.get_attribute('href')
            self.driver.execute_script(f"window.open('{href}', '_blank');")
            self.logger.info(f'Opened profile in new tab: {href}')
            return True
        except TimeoutException as e:
            self.logger.exception(f'Timed out waiting for element. Error: {str(e)}')
            return False
        except NoSuchElementException as e:
            self.logger.exception(f'Could not find required element. Error: {str(e)}')
            return False
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
                        # Scroll the tweet into view using Actions API
                        ActionChains(self.driver).scroll_to_element(tweet).perform()
                        sleep(0.5)  # Short wait for the scroll to complete
                        self.logger.info("Successfully scrolled to the latest non-ad and non-pinned post")
                        return tweet
                
                # If no suitable tweet found, scroll down
                self.driver.execute_script("window.scrollBy(0, 500);")
                sleep(0.5)  # Short wait for content to load
            
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

if __name__ == '__main__':
    browser = Browser(keep_open=True)  # Set keep_open to True
    browser.go_to_following('fakerfaker680')
    browser.open_profile_in_new_tab()
    browser.driver.switch_to.window(browser.driver.window_handles[-1])  # Switch to the newly opened tab
    tweet_element = browser.scroll_to_latest_post()
    if tweet_element:
        # Read the tweet content
        tweet_text = tweet_element.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
        print(f"Latest non-ad tweet content: {tweet_text}")
    else:
        print("Failed to find the latest non-ad and non-pinned tweet")

    if browser.keep_open:
        input("Press Enter to close the browser...")  # Wait for user input before closing
