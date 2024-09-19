from os import getenv
from dotenv import load_dotenv
from urllib.parse import urlparse
from datetime import datetime
from pymongo.mongo_client import MongoClient
from logger import logger

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        pwd = getenv('MONGO_PWD')
        connection_string = f"mongodb+srv://sammy:{pwd}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
        self.client = MongoClient(connection_string)
        self.db = self.client['auto_poster']
        self.tweets_collection = self.db['tweets']
        self.following_collection = self.db['following']
        self.logger = logger('database_manager')

    def save_tweet(self, tweet_link, username):
        parsed_url = urlparse(tweet_link)
        tweet_id = parsed_url.path.split('/')[-1]
        
        tweet_data = {
            'tweet_id': tweet_id,
            'tweet_link': tweet_link,
            'username': username,
            'timestamp': datetime.now()
        }
        
        result = self.tweets_collection.update_one(
            {'tweet_id': tweet_id},
            {'$set': tweet_data},
            upsert=True
        )
        
        if result.upserted_id:
            self.logger.info(f"Inserted new tweet: {tweet_id}")
        else:
            self.logger.info(f"Updated existing tweet: {tweet_id}")

    def save_profile(self, data: dict):
        '''This saves an X profile to the following collection in MongoDB if it doesn't already exist'''
        try:
            username = data.get('username')
            existing_profile = self.following_collection.find_one({'username': username})
            if existing_profile is None:
                self.following_collection.insert_one(data)
                self.logger.info(f"Successfully saved new profile for: {username}")
            else:
                self.logger.info(f"Profile for {username} already exists. Skipping insertion.")
        except Exception as e:
            self.logger.error(f"Failed to save profile. Error: {str(e)}")

    def is_profile_in_collection(self, link: str):
        '''This checks if a profile is in the following collection in MongoDB'''
        try:
            existing_profile = self.following_collection.find_one({'link': link})
            if existing_profile is None:
                return False
            else:
                return True
        except Exception as e:
            self.logger.error(f"Failed to check if profile is in collection. Error: {str(e)}")

    def get_following_list(self):
        '''This returns a list of all the profiles in the following collection in MongoDB'''
        try:
            following_list = list(self.following_collection.find({}))
            return following_list
        except Exception as e:
            self.logger.error(f"Failed to get following list. Error: {str(e)}")
            return []