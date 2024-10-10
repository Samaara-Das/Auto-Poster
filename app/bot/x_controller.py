from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from app.database.mongo_manager import MongoManager
from app.configuration.configuration import Config
from time import sleep
import app.decorators.decorators as decorators
from app.logger.logger import logger, clear_log_file

class VerificationRequiredException(Exception):
    """Custom exception for when verification is required during login."""
    pass

class XController:

    def __init__(self) -> None:
        clear_log_file()
        self.initialize_chrome_driver()
        self.driver.get("https://x.com/home")
        self.driver.maximize_window()
        self.window_handles = self.driver.window_handles
        self.logger = logger(__name__)
        self.db_manager = MongoManager()
        self.following = self.db_manager.get_following_list()
        self.added_people = self.db_manager.get_added_list()
        self.stop_get_following = False
        self.stop_add_process = False

        # Check if the account is locked after loading the home page
        self.is_account_locked = self.is_account_locked_page_open()
        if self.is_account_locked:
            self.logger.warning("Detected that the X account is locked.")

    def initialize_chrome_driver(self):
        '''This method initializes the Chrome driver and creates a `driver` attribute for the class'''
        chrome_options = Options() 
        chrome_options.add_experimental_option("detach", False)
        chrome_options.add_argument('--profile-directory=Profile 11') # This profile is for the fake account
        
        # Use a unique user data directory for this project
        chrome_options.add_argument(f"--user-data-dir={Config.CHROME_PROFILES_PATH}/AutoPoster")
        
        # Specify a different port for Chrome DevTools
        chrome_options.add_argument("--remote-debugging-port=9223")
        
        # Disable the use of a single Chrome instance
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Use a service object to set additional options
        service = ChromeService(executable_path=Config.CHROMEDRIVER_EXE_PATH)

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def check_user_exists(self, username):
        '''This method checks if the specified user exists on X. If the user exists, it returns the account name, otherwise it returns False.'''
        def check_stop_event():
            '''This checks if `self.stop_add_process` is True. If it is, `self.set_stop_add_process(False)` is called and True is returned. Otherwise, False is returned. It is intended to detect if the Add button in the Bot Targets tab was clicked.'''
            if self.stop_add_process:
                self.logger.info("Stop event detected. Setting stop_add_process to False")
                self.set_stop_add_process(False)
                return True
            return False
        
        try:
            # Navigate to the user's profile
            self.driver.get(f"https://x.com/{username}")
            
            if check_stop_event():
                return False

            # Wait for the page to load
            account_name = WebDriverWait(self.driver, 7).until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="UserName"]//span[@class="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3"]')))

            if check_stop_event():
                return False

            # Check if the user exists by checking if "@" is in the tab title
            user_exists = f"@" in self.driver.title
            if user_exists:
                self.logger.info(f'User {username} exists')
                return account_name.text
            else:
                self.logger.info(f'User {username} does not exist')
                return False
        except Exception as e:
            self.logger.exception(f"Error checking if user exists: {e}")
            return False

    def open_page(self, url: str):
        '''This opens `url` and maximizes the window'''
        try:
            self.driver.get(url)
            self.driver.set_window_size(1920, 1080)  # Set a large default size
            self.driver.maximize_window()
            if self.driver.get_window_size()['width'] < 1920:
                self.driver.fullscreen_window()
            self.logger.info(f'Opened this url: {url} and maximized the window')
            return True
        except WebDriverException:
            self.logger.exception(f'Cannot open this url: {url}')
            return False 

    @decorators.rest
    def sign_in(self, username, password, email):
        '''This method checks if the user is logged in to X, if not, it will sign in to the specified account'''
        self.driver.get('https://x.com/login') # go to X
        self.logger.info('Opened X login page')
        try:
            home_timeline = WebDriverWait(self.driver, 6).until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Home timeline"]')))
            if home_timeline.is_displayed(): # if the timeline is displayed, that means that X opened and a user is logged in
                self.logger.info('X login page redirected to home timeline')
                # check if the username on X is the same as the one that is passed as argument
                username_on_x = self.driver.find_element(By.XPATH, '//button[@aria-label="Account menu"]//span[contains(text(), "@")]').text
                if username_on_x.strip('@') == username:
                    self.logger.info(f'{username} is already logged in to X')
                else: # handle the case where a different account is logged in
                    self.logger.info(f'{username} is not logged in to X. Instead, {username_on_x} is logged in.')
                    self._logout()
                    self._login(username, password, email)
        except TimeoutException: # if the timeline is not displayed, that means that a user is not logged in
            self.logger.info('User is not logged in to X')
            self._login(username, password, email)

    @decorators.rest
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

    @decorators.rest
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

    def set_stop_add_process(self, stop_event):
        '''This method sets the boolean value of `self.stop_add_process` to `stop_event`'''
        self.stop_add_process = stop_event

    def update_added_people(self):
        '''This method fetches the latest data from the 'added' collection in MongoDB and updates `self.added_people`'''
        self.added_people = self.db_manager.get_added_list()

    def get_following_number(self, username: str):
        '''This method finds the number of people that the user is following on X'''
        try:
            self.open_page(f'https://x.com/{username}')
            sleep(2) # keep this sleep for the latest and correct following number to load
            following_element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, f'//div[@aria-label="Home timeline"]//a[@href="/{username}/following"]//span')))
            following_text = following_element.text.replace(',', '')
            
            # Handle the case where the number contains K. Eg: 32.1K or 12K
            if 'K' in following_text:
                following_text = following_text.replace('K', '')
                if '.' in following_text:
                    following_number = int(following_text) * 100
                else:
                    following_number = int(following_text) * 1000
            else:
                following_number = int(following_text)
            
            return following_number
            
        except Exception as e:
            self.logger.exception(f'Failed to get the number of people that the user is following on X. Error: {str(e)}')
            return 0

    def remove_person_from_db(self, link: str):
        '''This method removes a profile with `link` from the 'following' collection in MongoDB'''
        self.db_manager.delete_following_profile(link)

    def remove_added_person(self, link: str):
        '''This method removes a profile with `link` from `self.added_people`'''
        for person in self.added_people:
            if person['link'] == link:
                self.added_people.remove(person)
                break

    def go_to_following(self, username: str):
        '''This method goes to the following page of the specified user'''
        try:
            self.driver.get(f'https://x.com/{username}/following')
            self.logger.info(f'Successfully navigated to the following page of {username}')
            return True
        except Exception as e:
            self.logger.exception(f'Failed to navigate to the following page of {username}. Error: {str(e)}')
            return False

    def set_stop_get_following(self, stop_event):
        '''This method sets the boolean value of `self.stop_get_following` to `stop_event`'''
        self.stop_get_following = stop_event

    def get_following(self):
        """
        Goes through the following page and scrapes the data of the profiles that the user is following.
        Stores the data in MongoDB if it's not already present.
        """
        def check_stop_event():
            if self.stop_get_following:
                self.logger.info("Stop event detected. Setting stop_get_following to False")
                self.set_stop_get_following(False)
                return True
            return False

        try:
            timeline_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Timeline: Following"]'))
            )

            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_pause_time = 0.7
            latest_following = []

            while True:
                if check_stop_event():
                    self.logger.info("Aborting get_following.")
                    return True

                self.logger.info('Scrolling down to load more profiles')
                self.driver.execute_script("window.scrollBy(0, 600);")
                sleep(scroll_pause_time)

                profile_elements = timeline_div.find_elements(By.XPATH, './/div[@class="css-175oi2r r-1adg3ll r-1ny4l3l"]')
                self.logger.info(f'Scraping data from {len(profile_elements)} profiles')

                for element in profile_elements:
                    if check_stop_event():
                        self.logger.info("Aborting get_following.")
                        return True
                    try:
                        link = element.find_element(By.XPATH, './/a[@role="link"]').get_attribute('href')
                        if link not in latest_following:
                            latest_following.append(link)
                    except NoSuchElementException:
                        self.logger.warning("Profile link not found. Skipping.")
                        continue

                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # Try scrolling a bit more to ensure we've reached the bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sleep(scroll_pause_time)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # If heights are still the same, we've reached the end of the page
                        self.logger.info('Reached the end of the page')
                        break
                last_height = new_height

            self.logger.info(f"Scraped {len(latest_following)} profiles")
            
            for profile_link in latest_following:
                if check_stop_event():
                    self.logger.info("Aborting get_following.")
                    return True

                # store a profile that the user is following if it's not already in MongoDB
                if not self.db_manager.is_profile_in_following(profile_link): 
                    data = self.scrape_profile_data(profile_link)
                    self.following.append(data)
                    self.db_manager.save_profile(data)

            # Note: The logic for deleting a profile from the following collection if the user has unfollowed that profile is not implemented because papa told me to keep all the profiles that the user has ever followed.

            return True

        except TimeoutException:
            self.logger.warning("The page might not have loaded properly.")
            return False
        except Exception as e:
            self.logger.exception(f'Failed to scrape profile links. Error: {str(e)}')
            return False

    def unfollow_users(self, count):
        """
        Unfollows `count` users that the user is currently following. Removes people from the mongodb collection as they get unfollowed.
        """
        try:
            self.logger.info(f"Starting to unfollow {count} users.")
            timeline_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Timeline: Following"]'))
            )

            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_pause_time = 0.7
            unfollowed_profiles = []

            while True:
                profile_elements = timeline_div.find_elements(By.XPATH, './/div[@class="css-175oi2r r-1adg3ll r-1ny4l3l"]')
              
                for element in profile_elements:
                    if len(unfollowed_profiles) >= count: # if the desired number of profiles have been unfollowed, exit the method
                        self.logger.info(f"Finished unfollowing {count} users.")
                        return True
                    try:
                        link = element.find_element(By.XPATH, './/a[@role="link"]').get_attribute('href')
                        if link not in unfollowed_profiles:
                            # Click the Following button to trigger the Unfollow popup
                            button = element.find_element(By.XPATH, './/button[contains(@aria-label, "Following ")]')
                            if not button.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                sleep(0.5)  # Wait for scroll to complete
                            button.click()
                            unfollow_button = WebDriverWait(self.driver, 2).until(
                                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="confirmationSheetDialog"]//button[@data-testid="confirmationSheetConfirm"]'))
                            )
                            unfollow_button.click()
                            sleep(0.2)
                            unfollowed_profiles.append(link)
                            self.remove_person_from_db(link)
                    except WebDriverException as e:
                        self.logger.warning(f"WebDriverException occurred while clicking the unfollow button: {e}")
                        continue

                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # Try scrolling a bit more to ensure we've reached the bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sleep(scroll_pause_time)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # If heights are still the same, we've reached the end of the page
                        self.logger.info('Reached the end of the page')
                        break
                last_height = new_height

                self.logger.info('Scrolling down to load more profiles')
                self.driver.execute_script("window.scrollBy(0, 600);")
                sleep(scroll_pause_time)

        except TimeoutException:
            self.logger.warning("The page might not have loaded properly.")
            return False
        except Exception as e:
            self.logger.exception(f'Failed to unfollow users. Error: {str(e)}')
            return False

    def is_snackbar_displayed(self):
        """
        Checks if the snackbar indicating that you cannot follow more people is displayed.

        Returns:
            bool: True if the snackbar is displayed, False otherwise.
        """
        snackbar_selector = '//div[@data-testid="toast" and contains(.//span, "You are unable to follow more people at this time")]'
        try:
            snackbar = self.driver.find_element(By.XPATH, snackbar_selector)
            is_displayed = snackbar.is_displayed()
            return is_displayed
        except NoSuchElementException:
            # Snackbar not present
            return False
        except Exception as e:
            self.logger.exception(f"Error checking snackbar: {e}")
            return False

    @decorators.rest
    def auto_follow(self, keywords, follow_at_once, total_follow_count, total_followed, get_is_running):
        '''
        This method automatically follows users based on the given keywords and `follow_at_once` value.
        It returns the number of profiles followed.
        '''
        try:
            # Make all the keywords lowercase
            keywords = [keyword.lower() for keyword in keywords]

            # Wait for the profiles in the connect page to load
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//button[@data-testid="UserCell"]'))
            )

            # Selector for bio
            bio_selector = 'div[class="css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-1h8ys4a r-1jeg54m"]'

            # Initialize a set to keep track of profiles which have been checked
            processed_profiles = set()

            # Follow people if the specified keywords are in the profile's bio and the profile
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_pause_time = 0.7
            followed_profiles = 0
            total_followed_profiles = total_followed

            while True:
                profiles = self.driver.find_elements(By.XPATH, '//button[@data-testid="UserCell"]')
                for profile in profiles:
                    is_running = get_is_running()
                    if not is_running: # if the is_running attribute in AutoFollow is false, that means that the auto-follow process has stopped
                        return followed_profiles
                    
                    # Check for snackbar before attempting to follow
                    if self.is_snackbar_displayed():
                        self.logger.info('"You are unable to follow more people" snackbar displayed on X. Stopping auto-follow process')
                        return followed_profiles

                    try:
                        # Extract the profile link as a unique identifier
                        profile_link = profile.find_element(By.XPATH, './/a[@role="link"]').get_attribute('href')

                        # Skip the profile if it's already checked
                        if profile_link in processed_profiles:
                            continue

                        # Add the profile to processed profiles (this indicates that the profile has been checked)
                        processed_profiles.add(profile_link)

                        if total_followed_profiles >= total_follow_count:
                            # If the total follow count is reached, break the loop
                            self.logger.info(f"Reached total follow count of {total_follow_count}")
                            return followed_profiles

                        if followed_profiles >= follow_at_once:
                            # If the follow at once limit is reached, break the loop
                            self.logger.info(f"Reached follow at once limit of {follow_at_once}")
                            return followed_profiles

                        # Get the bio of the profile
                        try:
                            bio = profile.find_element(By.CSS_SELECTOR, bio_selector).text.lower()
                            self.logger.debug(f"Profile bio: {bio}")
                        except NoSuchElementException:
                            bio = ""
                            self.logger.debug("No bio found for this profile.")

                        # Check if any keyword is in bio if the keywords list is not empty.
                        # If any keyword is in the bio, follow the profile
                        if not keywords or any(f' {keyword} ' in bio for keyword in keywords):
                            try:
                                follow_button = profile.find_element(By.XPATH, './/button[contains(@aria-label, "Follow ")]')

                                # If the button isn't displayed, scroll the profile into view
                                if not follow_button.is_displayed():
                                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", profile)
                                    sleep(0.5)

                                follow_button.click()
                                sleep(0.2)  # Short pause after each follow
                                followed_profiles += 1
                                total_followed_profiles += 1
                    
                            except Exception as e:
                                self.logger.exception(f"Unexpected error when trying to follow: {e}")

                    except NoSuchElementException:
                        self.logger.warning("Profile link element not found. Skipping this profile.")
                        continue
                    except Exception as e:
                        self.logger.exception(f"Error processing a profile: {e}")
                        continue

                # Scroll down to load more profiles
                self.driver.execute_script("window.scrollBy(0, 500);")
                sleep(scroll_pause_time)

                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    self.logger.info("Reached the end of the page or no new profiles loaded.")
                    break
                last_height = new_height

            self.logger.info(f"auto-follow process complete. Followed {followed_profiles} profiles.")
            return followed_profiles

        except TimeoutException:
            self.logger.warning('Failed to auto follow because of timeout exception')
            return followed_profiles
        except Exception as e:
            self.logger.exception(f'Failed to auto follow. Error: {str(e)}')
            return followed_profiles

    @decorators.rest
    def scrape_profile_data(self, link) -> dict:
        """
        Scrapes and returns data of an X profile.
        """
        def check_stop_event():
            '''This checks if `self.stop_add_process` is True. If it is, `self.set_stop_add_process(False)` is called and True is returned. Otherwise, False is returned. It is intended to detect if the Add button in the Bot Targets tab was clicked.'''
            if self.stop_add_process:
                self.logger.info("Stop event detected. Setting stop_add_process to False")
                self.set_stop_add_process(False)
                return True
            return False
        
        try:
            # Open the profile in a new tab
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(link)
            self.logger.info(f'Opened {link} in new tab')

            if check_stop_event():
                return None

            self.reload_page()

            # Wait for the page to load
            name_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="UserName"]'))
            )

            # Extract profile data
            profile = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="css-175oi2r r-3pj75a r-ttdzmv r-1ifxtd0"]'))
            )
            
            username = link.split('com/')[1]
            name = name_element.text.split('@')[0].strip()
            following_count = profile.find_element(By.XPATH, './/a[contains(@href, "/following")]/span/span').text
            followers_count = profile.find_element(By.XPATH, './/a[contains(@href, "followers")]/span/span').text

            if check_stop_event():
                return None

            # Optional fields
            bio = self._get_optional_field(profile, '//div[@data-testid="UserDescription"]')
            location = self._get_optional_field(profile, '//div[@data-testid="UserProfileHeader_Items"]//span[@data-testid="UserLocation"]')
            website = self._get_optional_field(profile, '//div[@data-testid="UserProfileHeader_Items"]//a[@data-testid="UserUrl"]', attr='href')
            self.logger.info(f'Successfully scraped data from {username}')

            # Scrape the followers the user is following
            try:
                WebDriverWait(profile, 1.2).until(EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Not followed by anyone you’re following")]')))
                self.logger.info(f"{username} is not followed by anyone you're following.")
                followers_you_follow = []
            except TimeoutException:
                followers_you_follow = self._fetch_followers_you_follow()
                # click the back button amd wait for the profile page to load
                self.driver.find_element(By.XPATH, '//div[@aria-label="Home timeline"] //button[@aria-label="Back"]').click()
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="UserName"]')))

            # Click the View More button if it exists
            try:
                if check_stop_event():
                    return None
                
                more_info = ''
                view_more_button = self.driver.find_element(By.XPATH, '//div[@class="css-175oi2r r-3pj75a r-ttdzmv r-1ifxtd0"] //a[contains(@href, "bio")]')
                view_more_button.click()
                more_info = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="extended-profile"]'))
                ).text
            except TimeoutException as te:
                self.logger.info(f"Timeout while clicking the 'View More' button: {te}")    
            except Exception as e:
                self.logger.info("No 'View More' button found")

            profile_data = {
                'username': username,
                'name': name,
                'link': link,
                'following_count': following_count,
                'followers_count': followers_count,
                'bio': bio,
                'location': location,
                'website': website,
                'followers_you_follow': followers_you_follow,
                'more_info': more_info,
                'reply': True,  # Default to True when adding a new profile
            }

            # Return the profile data for further use
            self.close_current_tab()
            return profile_data

        except TimeoutException as te:
            self.logger.error(f"Timeout while loading profile data: {te}")
            self.close_current_tab()
        except NoSuchElementException as nse:
            self.logger.error(f"Element not found while storing profile data: {nse}")
            self.close_current_tab()
        except Exception as e:
            self.logger.exception(f"Failed to store profile data. Error: {str(e)}")
            self.close_current_tab()
            return None

    def _get_optional_field(self, profile, xpath, attr=None):
        """
        Helper method to fetch optional fields like location and website.
        """
        try:
            element = profile.find_element(By.XPATH, xpath)
            return element.get_attribute(attr) if attr else element.text
        except NoSuchElementException:
            self.logger.info(f"Optional field not found for xpath: {xpath}")
            return ''

    @decorators.rest
    def _fetch_followers_you_follow(self):
        """
        Fetches the list of followers you follow.
        """
        def check_stop_event():
            '''This checks if `self.stop_add_process` is True. If it is, True is returned. Otherwise, False is returned. It is intended to detect if the Add button in the Bot Targets tab was clicked.'''
            if self.stop_add_process:
                self.logger.info("Stop event detected.")
                return True
            return False
        
        try:
            # Navigate to the 'Followers you know' page
            if check_stop_event():
                return []
            
            common_followers_link = self.driver.find_element(By.XPATH, '//a[@aria-label="Followers you know"]').get_attribute('href')
            self.driver.get(common_followers_link)
            followers_section = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Timeline: Followers you know"]'))
            )

            self.logger.info('Scraping the list of followers that you know')
            followers_you_follow = set()  # Use a set to automatically handle duplicates
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_pause_time = 0.7
            while True:
                if check_stop_event():
                    return []
                
                self.logger.info('Scrolling down to load more profiles')
                self.driver.execute_script("window.scrollBy(0, 500);")
                sleep(scroll_pause_time)

                # Fetch follower usernames
                username_elements = followers_section.find_elements(By.XPATH, '//button[@data-testid="UserCell"] //span[contains(text(), "@")]')
                new_followers = set(elem.text.strip('@') for elem in username_elements)
                followers_you_follow.update(new_followers)

                # Check if we've reached the bottom or if we haven't found new followers in several scrolls
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # Try a final scroll to ensure
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sleep(scroll_pause_time)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        self.logger.info('Reached the bottom of the page')
                        break
                last_height = new_height

            self.logger.info(f"Scraped {len(followers_you_follow)} followers you follow")
            return list(followers_you_follow)

        except TimeoutException as te:
            self.logger.error(f"Timeout while fetching followers you follow: {te}")
            return []
        except NoSuchElementException as nse:
            self.logger.error(f"Element not found while fetching followers you follow: {nse}")
            return []
        except Exception as e:
            self.logger.exception(f"Error while fetching followers you follow: {e}")
            return []

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
            max_attempts = 5
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

    def reload_page(self, mins_to_wait=3):
        """
        If the Retry button is found, we wait for a minute, refresh the page and wait for the page to fully load.
        """
        try:
            # check if the Retry button is present on the page
            retry_span = self.driver.find_element(By.XPATH, '//div[@data-testid="primaryColumn"] //span[text()="Retry"]')
            self.logger.info(f"Retry button found. Will sleep for {mins_to_wait} minutes before reloading the page.")
            mins = mins_to_wait * 60
            sleep(mins) # sleep for 2 minutes
            self.driver.refresh()
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="primaryColumn"]')))
            sleep(2)
            return True
        except NoSuchElementException:
            self.logger.info("No Retry button found, no need to reload the page")
            return True
        except Exception as e:
            self.logger.exception(f"Failed to reload the page. Error: {str(e)}")
            return False
    
    def get_tweet_link(self, tweet_element):
        """
        Extracts the tweet link from the given tweet element.
        """
        try:
            link_element = tweet_element.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
            link = link_element.get_attribute('href')
            self.logger.info(f'Successfully found tweet link: {link}')
            return link
        except NoSuchElementException:
            self.logger.error("Could not find tweet link")
            return None

    def get_tweet_author(self, tweet_element):
        """
        Extracts the username of the tweet author from the given tweet element.
        """
        try:
            author_element = tweet_element.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span[contains(text(), "@")]')
            author = author_element.text.strip('@')
            self.logger.info(f'Successfully found tweet author: {author}')
            return author
        except NoSuchElementException:
            self.logger.error("Could not find tweet author")
            return None

    @decorators.rest
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

    @decorators.rest
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

    @decorators.rest
    def send_reply(self):
        """
        Clicks the send button for the reply.
        """
        try:
            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="tweetButton"]'))
            )
            send_button.click()
            self.logger.info("Successfully clicked the reply send button")
            return True
        except TimeoutException:
            self.logger.exception(f"Failed to click reply send button. Error: TimeoutException")
            return False
        except Exception as e:
            self.logger.exception(f"Failed to click reply send button. Error: {str(e)}")
            return False

    @decorators.rest
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

    def close_browser(self):
        """
        Closes the browser safely.
        """
        try:
            if self.driver:
                self.driver.stop_client()
                self.driver.close()
                self.driver.quit()
            self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.exception(f"Error closing browser: {str(e)}")

    def is_account_locked_page_open(self):
        """
        Checks if the "Your account has been locked" page is displayed.
        """
        try:
            self.driver.get('https://x.com/account/access')

            # Check if the "Your account has been locked" page is displayed
            locked_message = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Your account has been locked.")]'))
            )
            
            if locked_message:
                self.logger.info("Account locked page detected")
                return True
            
        except TimeoutException:
            self.logger.warning("Account locked page not detected or elements not found")
            return False
        except Exception as e:
            self.logger.exception(f"Error checking if account is locked: {str(e)}")
            return False


