# import modules
from time import sleep, time
from logger import logger, clear_log_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException

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
   
    def open_page(self, url: str):
        '''This opens `url` and maximizes the window'''
        try:
            self.driver.get(url)
            self.logger.info(f'Opened this url: {url}')
            self.driver.maximize_window()
            return True
        except WebDriverException:
            self.logger.exception(f'Cannot open this url: {url}. Error: ')
            return False 
        
    def go_to_following(self, username: str):
        self.driver.get(f'https://x.com/{username}/following')

if __name__ == '__main__':
    browser = Browser(keep_open=True)
    browser.go_to_following('fakerfaker680')
    