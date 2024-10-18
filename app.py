import re
import emoji
from googleapiclient.discovery import build
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

API_KEY = 'xxxxxxxxxxxxxxxxxxxxxx'  # Put in your API Key

youtube = build('youtube', 'v3', developerKey=API_KEY)  # Initializing Youtube API

# Taking input from the user and slicing for video id
video_id = input('Enter Youtube Video URL: ')[-11:]
print("Video ID: " + video_id)

# Getting the channelId of the video uploader
video_response = youtube.videos().list(part='snippet', id=video_id).execute()

# Splitting the response for channelID
video_snippet = video_response['items'][0]['snippet']
uploader_channel_id = video_snippet['channelId']
print("Channel ID: " + uploader_channel_id)

# Fetch comments and filter out those by the uploader and non-English comments
print("Fetching Comments...")

comments = []
nextPageToken = None

def is_english(comment_text):
    # Filter out non-English comments by checking the Unicode range for English characters
    return re.match(r'^[\x00-\x7F]+$', comment_text) is not None

try:
    # Loop until we have at least 600 comments or until we run out of comments to fetch
    while len(comments) < 200:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,  # Fetch up to 100 comments per request
            pageToken=nextPageToken
        )
        
        response = request.execute()

        # Loop through the items (comments) in the response
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            # Check if the comment is not from the video uploader and is in English
            comment_text = comment['textDisplay']
            if comment['authorChannelId']['value'] != uploader_channel_id and is_english(comment_text):
                comments.append(comment_text)

        nextPageToken = response.get('nextPageToken')

        if not nextPageToken:
            break

except Exception as e:
    print("Error occurred:", str(e))

# Display the first 5 fetched comments, if any
if comments:
    print("First 5 comments (English only, excluding uploader):")
    for i, comment in enumerate(comments[:5], start=1):
        print(f"{i}: {comment}")
else:
    print("No comments fetched.")

# Define a pattern to match hyperlinks
hyperlink_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

# Define the threshold ratio for filtering emojis
threshold_ratio = 0.65

# List to store relevant comments
relevant_comments = []

# Loop through each comment in the fetched comments
for comment_text in comments:
    
    # Convert comment to lowercase and remove leading/trailing spaces
    comment_text = comment_text.lower().strip()

    # Count the number of emojis in the comment
    emojis = emoji.emoji_count(comment_text)

    # Count text characters (excluding spaces)
    text_characters = len(re.sub(r'\s', '', comment_text))

    # Check if the comment contains any alphanumeric characters and no hyperlinks
    if (any(char.isalnum() for char in comment_text)) and not hyperlink_pattern.search(comment_text):
        
        # Filter out comments that are mostly emojis
        if emojis == 0 or (text_characters / (text_characters + emojis)) > threshold_ratio:
            relevant_comments.append(comment_text)

# Print the first 5 relevant comments
print("First 5 relevant comments:")
for i, comment in enumerate(relevant_comments[:5], start=1):
    print(f"{i}: {comment}")

# Write relevant comments to a file
with open("ytcomments.txt", 'w', encoding='utf-8') as f:
    for idx, comment in enumerate(relevant_comments):
        f.write(str(comment) + "\n")

print("Comments stored successfully!")

# Function to analyze sentiment scores and append to polarity
def sentiment_scores(comment, polarity):
    sentiment_object = SentimentIntensityAnalyzer()
    sentiment_dict = sentiment_object.polarity_scores(comment)
    polarity.append(sentiment_dict['compound'])
    return polarity

polarity = []
positive_comments = []
negative_comments = []
neutral_comments = []

# Read comments from the file
with open("ytcomments.txt", 'r', encoding='utf-8') as f:
    comments = f.readlines()

# Analyze the comments
print("Analyzing Comments...")

for comment in comments:
    polarity = sentiment_scores(comment, polarity)
    if polarity[-1] > 0.05:
        positive_comments.append(comment)
    elif polarity[-1] < -0.05:
        negative_comments.append(comment)
    else:
        neutral_comments.append(comment)

print("Polarity scores:", polarity[:5])

# Calculate the average polarity score
avg_polarity = sum(polarity) / len(polarity)
print("Average Polarity:", avg_polarity)

# Categorize the video response based on average polarity
if avg_polarity > 0.05:
    print("The Video has a Positive response")
elif avg_polarity < -0.05:
    print("The Video has a Negative response")
else:
    print("The Video has a Neutral response")

# Find the most positive and most negative comments
most_positive_comment = comments[polarity.index(max(polarity))]
most_negative_comment = comments[polarity.index(min(polarity))]

print("Most Positive Comment:", most_positive_comment.strip(), "Score:", max(polarity))
print("Most Negative Comment:", most_negative_comment.strip(), "Score:", min(polarity))

# Count positive, negative, and neutral comments
positive_count = len(positive_comments)
negative_count = len(negative_comments)
neutral_count = len(neutral_comments)

# Bar Chart
plt.bar(['Positive', 'Negative', 'Neutral'], [positive_count, negative_count, neutral_count], color=['blue', 'red', 'grey'])
plt.xlabel('Sentiment')
plt.ylabel('Comment Count')
plt.title('Sentiment Analysis of Comments')
plt.show()

# Pie Chart
plt.figure(figsize=(10, 6))
plt.pie([positive_count, negative_count, neutral_count], labels=['Positive', 'Negative', 'Neutral'], autopct='%1.1f%%', startangle=90)
plt.axis('equal')
plt.show()
