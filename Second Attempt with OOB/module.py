# Import necessary libraries
import os
import sqlite3
import base64
import re
import requests
import tweepy
from textblob import TextBlob

# Load environment variables
api_key = os.getenv('Key_Twitter')
api_secret = os.getenv('Secret_Key_Twitter')
client_id = os.getenv('Client_ID')
client_secret = os.getenv('Client_Secret')
access_token = os.getenv('Token')
access_secret = os.getenv('Secret_Token')
bearer_token = os.getenv('Bearer_Token')

# Define the TwitterAPI class


class TwitterAPI:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base64_encoded_key = self.encode_api_keys()

    def encode_api_keys(self):
        api_key_secret = f'{self.api_key}:{self.api_secret}'
        return base64.b64encode(api_key_secret.encode('utf-8')).decode('utf-8')

    def get_bearer_token(self):
        url = 'https://api.twitter.com/oauth2/token'
        headers = {
            'Authorization': f'Basic {self.base64_encoded_key}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        data = {'grant_type': 'client_credentials'}

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f'Error getting Bearer Token: {response.status_code}')
            return None

# Define the TwitterSearch class


class TwitterSearch:
    def __init__(self, bearer_token, query, max_tweets):
        self.bearer_token = bearer_token
        self.query = query
        self.max_tweets = max_tweets
        self.data = self.search_tweets()

    def search_tweets(self):
        url = f'https://api.twitter.com/2/tweets/search/recent?query={self.query}&max_results={self.max_tweets}'
        headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error searching tweets: {response.status_code}')
            return None


class Actions:
    @staticmethod
    def clean_tweet_text(text):
        cleaned_text = re.sub(
            r'http\S+|@\w+|#\w+|[^\w\s]|(\s+)', ' ', text).strip()
        return cleaned_text

    @staticmethod
    def tokenize_and_lowercase(cleaned_text):
        tokens = cleaned_text.lower().split()
        return tokens

    @staticmethod
    def preprocess(text):
        cleaned = Actions.clean_tweet_text(text)
        tokens = Actions.tokenize_and_lowercase(cleaned)
        return tokens

    def perform_sentiment_analysis(self, text):
        tokens = Actions.preprocess(text)
        # Assuming you want to calculate sentiment for each token
        sentiment_values = [TextBlob(token).sentiment for token in tokens]

        # Extract polarity and subjectivity values
        polarities = [item.polarity for item in sentiment_values]
        subjectivities = [item.subjectivity for item in sentiment_values]

        sentiment_data = {
            'Text': tokens,
            'Sentiment': polarities,
            'Sentiment_Magnitude': subjectivities
        }
        return sentiment_data


# Define the Database class
class Database:
    def search_and_store_tweets(self, api, query, max_tweets=10):
        # Connect to the SQLite database
        conn = sqlite3.connect('tweets.db')
        cursor = conn.cursor()

        # Create a table to store tweet data if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tweets (
                text TEXT,
                Sentiment_VADER REAL;
            )
        ''')

        # Search for tweets and store them in the database
        tweet_count = 0
        for tweet in tweepy.Cursor(api.search_recent_tweets, q=query, max_results=max_tweets).items(max_tweets):
            tweet_data = (
                tweet.id,
                tweet.text,
                tweet.created_at,
                tweet.user.username,
                tweet.user.followers_count
            )
            cursor.execute(
                'INSERT INTO tweets VALUES (?, ?, ?, ?)', tweet_data)
            tweet_count += 1

        # Commit changes and close the database connection
        conn.commit()
        conn.close()

        return tweet_count

# Show all records in the database


def show_all_records(db_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get the list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tables = cursor.fetchall()

    # Loop through all tables and print out their records
    for table in tables:
        table_name = table[0]
        print(f"Records from table {table_name}:")

        cursor.execute(f"SELECT * FROM {table_name};")
        records = cursor.fetchall()

        for record in records:
            print(record)
        print("\n")

    # Close the connection
    conn.close()
