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
        self.collection = self.db['tweets']
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
        
        result = self.collection.update_one(
            {'tweet_id': tweet_id},
            {'$set': tweet_data},
            upsert=True
        )
        
        if result.upserted_id:
            self.logger.info(f"Inserted new tweet: {tweet_id}")
        else:
            self.logger.info(f"Updated existing tweet: {tweet_id}")