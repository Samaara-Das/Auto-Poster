# app/config.py
import os

class Config:
    MONGODB_PWD = os.getenv('MONGODB_PWD')
    CHROMEDRIVER_EXE_PATH = os.getenv('CHROMEDRIVER_EXE_PATH')
    CHROME_PROFILES_PATH = os.getenv('CHROME_PROFILES_PATH')
    DATABASE_URI ='mongodb+srv://sammy:{}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1'.format(MONGODB_PWD)
    LOG_FILE = 'app_log.log'
    TIME_SPAN = 4 # minutes needed for the bot to auto follow
    FOLLOW_DURATION = 1 # duration to follow a single person in seconds (for auto follow)
