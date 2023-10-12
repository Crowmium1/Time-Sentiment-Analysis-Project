import os
import sqlite3
import base64
import re
from dash import Dash
import requests
from textblob import TextBlob
from textblob.sentiments import PatternAnalyzer
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from module import TwitterAPI, TwitterSearch, show_all_records

# nltk.download('vader_lexicon')

# Initialize the Dash app
app = Dash(__name__)

# Load environment variables
api_key = os.getenv('Key_Twitter')
api_secret = os.getenv('Secret_Key_Twitter')

# Encode the API key and API secret key in base64 format
api_key_secret = f'{api_key}:{api_secret}'
base64_encoded_key = base64.b64encode(
    api_key_secret.encode('utf-8')).decode('utf-8')

# Define the URL to get the Bearer Token
url = 'https://api.twitter.com/oauth2/token'

# Define the headers with Authorization
headers = {
    'Authorization': f'Basic {base64_encoded_key}',
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
}

# Define the data for the POST request
data = {'grant_type': 'client_credentials'}

# Make the POST request to get the Bearer Token
response = requests.post(url, headers=headers, data=data, timeout=10)

# Parse the JSON response and extract the access token
bearer_token = response.json().get('access_token')

# Check if the Bearer Token was obtained successfully
if not bearer_token:
    print('Error: Failed to obtain Bearer Token.')
    exit()

# CREATE Table
conn = sqlite3.connect('tweets.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweets (
        Text TEXT,
        Sentiment REAL,
        Sentiment_Magnitude REAL,
        Sentiment_VADER REAL
    )
''')
conn.commit()

# Query Parameters
query = 'football'
max_tweets = 10
url = f'https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_tweets}'
headers = {
    'Authorization': f'Bearer {bearer_token}'
}

# Make the GET request with a timeout of 10 seconds
response = requests.get(url, headers=headers, timeout=10)

# # Parse and print the response
# if response.status_code == 200:
#     data = response.json()
#     print(data)
# else:
#     print(f'Error: {response.status_code}')

# Parse the response JSON
if response.status_code == 200:
    data = response.json()
    tweets = [data_item.get('text', '') for data_item in data.get('data', [])]
else:
    print(f'Error: {response.status_code}')

# Create a DataFrame from the extracted tweets with Sentiment and Sentiment_Magnitude columns
df = pd.DataFrame({'text': tweets, 'Sentiment': 0.0,
                  'Sentiment_Magnitude': 0.0})

# Create a separate DataFrame to store sentiment analysis results
sentiment_df = pd.DataFrame(
    columns=['Sentiment_TextBlob', 'Sentiment_Magnitude_TextBlob', 'Sentiment_VADER'])

# Store, clean, and analyze tweets to the dataframe and the database
tweet_count = 0
max_tweets = 100  # Define your maximum tweet count here

# Connect to the database outside the loop
conn = sqlite3.connect('tweets.db')
cursor = conn.cursor()

# Define a function to analyze sentiment using TextBlob with Pattern Analyzer


def analyze_sentiment_pattern(text):
    blob = TextBlob(text, analyzer=PatternAnalyzer())
    return blob.sentiment.polarity, blob.sentiment.subjectivity


def clean_text(text):
    # Remove URLs, mentions, hashtags, and special characters (excluding spaces) from the beginning of sentences
    cleaned_text = re.sub(r'http\S+|@\w+|#\w+|[^\w\s]|(^|\s)@', ' ', text)
    return cleaned_text.strip()


# Apply the clean_text function to the 'text' column
df['text'] = df['text'].apply(clean_text)

# Initialize the VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Create an empty list to store DataFrames
dataframes = []

# Iterate through the DataFrame and update sentiment scores
for data, row in df.iterrows():
    cleaned_text = row['text']

    # Perform sentiment analysis using TextBlob with Pattern Analyzer
    sentiment, sentiment_magnitude = analyze_sentiment_pattern(cleaned_text)

    # Perform sentiment analysis using VADER
    sentiment_vader = analyzer.polarity_scores(cleaned_text)['compound']

    # Update the database
    tweet_data = (cleaned_text, sentiment,
                  sentiment_magnitude, sentiment_vader)
    cursor.execute(
        'INSERT INTO tweets (Text, Sentiment, Sentiment_Magnitude, Sentiment_VADER) VALUES (?, ?, ?, ?)', tweet_data)

    # Create a DataFrame for the current row
    current_df = pd.DataFrame({
        'Text': [cleaned_text],
        'Sentiment_Textblob_Polarity': [sentiment],
        'Sentiment_Textblob_Subjectivity': [sentiment_magnitude],
        'Sentiment_VADER': [sentiment_vader]
    })

    # Append the current DataFrame to the list
    dataframes.append(current_df)

    tweet_count += 1

    if tweet_count >= max_tweets:
        break

# Concatenate all DataFrames in the list into a single DataFrame
sentiment_df = pd.concat(dataframes, ignore_index=True)

# Commit and close the database connection
conn.commit()
conn.close()

if tweet_count > 0:
    print(f'Successfully stored {tweet_count} tweets in the database.')
else:
    print('No tweets found or stored.')

# # Now, sentiment_df contains the sentiment analysis results
# print(sentiment_df)

# # Show all records in the database
# show_all_records('C:\Users\ljfit\Desktop\Coding Projects\Time Sentiment Analysis of social media for Brand Monitoring\Project Folder\tweets.db')
