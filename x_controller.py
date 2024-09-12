from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from os import getenv
from dotenv import load_dotenv
from time import sleep
import json
from logger import logger, clear_log_file

# Load environment variables
load_dotenv()

# Replace the hardcoded values with environment variables
CHROMEDRIVER_EXE_PATH = getenv('CHROMEDRIVER_EXE_PATH')
CHROME_PROFILES_PATH = getenv('CHROME_PROFILES_PATH')

class VerificationRequiredException(Exception):
    """Custom exception for when verification is required during login."""
    pass

class XController:

    def __init__(self) -> None:
        clear_log_file()
        chrome_options = Options() 
        chrome_options.add_experimental_option("detach", False)
        chrome_options.add_argument('--profile-directory=Profile 11') # This profile is for the fake account
        
        # Use a unique user data directory for this project
        chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILES_PATH}/AutoPoster")
        
        # Specify a different port for Chrome DevTools
        chrome_options.add_argument("--remote-debugging-port=9223")
        
        # Disable the use of a single Chrome instance
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Use a service object to set additional options
        service = ChromeService(executable_path=CHROMEDRIVER_EXE_PATH)

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.get("https://x.com/home")
        self.driver.maximize_window()
        self.window_handles = self.driver.window_handles
        self.logger = logger(__name__)
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

    def sign_in(self, username, password, email):
        '''This method checks if the user is logged in to X, if not, it will sign in to the specified account'''
        self.driver.get('https://x.com/login') # go to X
        try:
            home_timeline = WebDriverWait(self.driver, 6).until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Home timeline"]')))
            if home_timeline.is_displayed(): # if the timeline is displayed, that means that X opened and a user is logged in
                # check if the username on X is the same as the one that is passed as argument
                account_menu = self.driver.find_element(By.XPATH, '//button[@aria-label="Account menu"]')
                username_on_x = account_menu.find_element(By.XPATH, '//button[@aria-label="Account menu"]//span[contains(text(), "@")]').text
                if username_on_x.strip('@') == username:
                    self.logger.info('User is already logged in to X')
                else: # handle the case where a different account is logged in
                    self._logout()
                    self._login(username, password, email)
        except TimeoutException: # if the timeline is not displayed, that means that a user is not logged in
            self.logger.info('User is not logged in to X')
            self._login(username, password, email)

    def _logout(self):
        '''Helper method to log out the current user'''
        self.logger.info('Logging out the current user')
        account_menu = self.driver.find_element(By.XPATH, '//button[@aria-label="Account menu"]')
        account_menu.click()
        sleep(1)
        logout_button = self.driver.find_element(By.XPATH, '//a[@href="/logout"]')
        logout_button.click()
        sleep(1)
        confirm_logout_button = self.driver.find_element(By.XPATH, '//button[@data-testid="confirmationSheetConfirm"]')
        confirm_logout_button.click()
        sleep(1)
        login_button = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '//a[@data-testid="loginButton"]')))
        login_button.click()

    def _login(self, username, password, email):
        '''Helper method to perform the actual login process'''
        try:
            # Find and enter username
            username_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '//input[@autocomplete="username"]')))
            username_input.send_keys(username)
            username_input.send_keys(Keys.ENTER)
            self.logger.info('Successfully entered username')

            # If a phone number or email is required because suspicious activity is detected, enter the email
            try:
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Enter your phone number or email address")]')))
                email_input = self.driver.find_element(By.XPATH, '//input[@data-testid="ocfEnterTextTextInput"]')
                email_input.send_keys(email)
                email_input.send_keys(Keys.ENTER)
                self.logger.info('Successfully entered email')
            except TimeoutException: # if a timeout exception is raised, that means that the popup asking for email or phone number didn't display
                self.logger.info('No popup asking for email or phone number')
                pass
            
            # Wait for password input to be present
            password_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '//input[@name="password"]')))
            password_input.send_keys(password)
            password_input.send_keys(Keys.ENTER)
            self.logger.info('Successfully entered password')

            # Check for verification popup
            try:
                WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "verification")]')))
                raise VerificationRequiredException("Verification required for X account. All two-factor authentication methods for X account should be disabled.")
            except TimeoutException:
                # Verification popup not found, continue with login process
                self.logger.info('No verification popup')
                pass

            # Wait for the home timeline to be present, indicating successful login
            WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Home timeline"]')))
            self.logger.info('Successfully logged in to X')
        except VerificationRequiredException as ve:
            self.logger.error(str(ve))
            raise  # Re-raise the exception to be caught by the calling method
        except Exception as e:
            self.logger.exception(f'Failed to log in to X. Error: {str(e)}')
            raise  # Re-raise the exception to be caught by the calling method

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
                    self.window_handles = self.driver.window_handles
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

        except TimeoutException:
            self.logger.warning("Timeline not found. The page might not have loaded properly.")
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
