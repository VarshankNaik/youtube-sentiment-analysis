# For Fetching Comments 
from googleapiclient.discovery import build 
# For filtering comments 
import re 
# For filtering comments with just emojis 
import emoji
# Analyze the sentiments of the comment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# For visualization 
import matplotlib.pyplot as plt

API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxx'# Put in your API Key

youtube = build('youtube', 'v3', developerKey=API_KEY) # initializing Youtube API

# Taking input from the user and slicing for video id
video_id = input('Enter Youtube Video URL: ')[-11:]
print("video id: " + video_id)

# Getting the channelId of the video uploader
video_response = youtube.videos().list(
	part='snippet',
	id=video_id
).execute()

# Splitting the response for channelID
video_snippet = video_response['items'][0]['snippet']
uploader_channel_id = video_snippet['channelId']
print("channel id: " + uploader_channel_id)

# Fetch comments
# print("Fetching Comments...")
# comments = []
# nextPageToken = None
# while len(comments) < 600:
# 	request = youtube.commentThreads().list(
# 		part='snippet',
# 		videoId=video_id,
# 		maxResults=100, # You can fetch up to 100 comments per request
# 		pageToken=nextPageToken
# 	)
# 	response = request.execute()
# 	for item in response['items']:
# 		comment = item['snippet']['topLevelComment']['snippet']
# 		# Check if the comment is not from the video uploader
# 		if comment['authorChannelId']['value'] != uploader_channel_id:
# 			comments.append(comment['textDisplay'])
# 	nextPageToken = response.get('nextPageToken')

# 	if not nextPageToken:
# 		break
# # Print the 5 comments
# comments[:5]


# Fetch comments and filter out those by the uploader
print("Fetching Comments...")

# Initialize a list to store the comments
comments = []
nextPageToken = None

try:
    # Loop until we have at least 600 comments
    while len(comments) < 600:
        # Request to get comment threads
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,  # Fetch up to 100 comments per request
            pageToken=nextPageToken
        )
        
        # Execute the request
        response = request.execute()

        # Debugging: Print the response to inspect it
        print("API Response: ", response)

        # Loop through the items (comments) in the response
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            # Check if the comment is not from the video uploader
            if comment['authorChannelId']['value'] != uploader_channel_id:
                # Append the comment's text to the comments list
                comments.append(comment['textDisplay'])

        # Check if there's a next page of comments
        nextPageToken = response.get('nextPageToken')

        # Break the loop if there are no more comments to fetch
        if not nextPageToken:
            break

except Exception as e:
    # Print out any errors encountered
    print("Error occurred:", str(e))

# Display the first 5 fetched comments, if any
if comments:
    print("First 5 comments (excluding uploader):")
    for i, comment in enumerate(comments[:5], start=1):
        print(f"{i}: {comment}")
else:
    print("No comments fetched.")

# hyperlink_pattern = re.compile(
# 	r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

# threshold_ratio = 0.65

# relevant_comments = []

# # Inside your loop that processes comments
# for comment_text in comments:

# 	comment_text = comment_text.lower().strip()

# 	emojis = emoji.emoji_count(comment_text)

# 	# Count text characters (excluding spaces)
# 	text_characters = len(re.sub(r'\s', '', comment_text))

# 	if (any(char.isalnum() for char in comment_text)) and not hyperlink_pattern.search(comment_text):
# 		if emojis == 0 or (text_characters / (text_characters + emojis)) > threshold_ratio:
# 			relevant_comments.append(comment_text)

# # Print the relevant comments
# relevant_comments[:5]

# Define a pattern to match hyperlinks
hyperlink_pattern = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

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

# Open the file in write mode with utf-8 encoding
with open("ytcomments.txt", 'w', encoding='utf-8') as f:
    # Loop through the filtered relevant comments and write each to the file
    for idx, comment in enumerate(relevant_comments):
        f.write(str(comment) + "\n")

# Print a success message after storing the comments
print("Comments stored successfully!")

# Function to analyze sentiment scores and append to polarity
def sentiment_scores(comment, polarity):
    # Creating a SentimentIntensityAnalyzer object
    sentiment_object = SentimentIntensityAnalyzer()

    # Getting the polarity scores (positive, negative, neutral, and compound)
    sentiment_dict = sentiment_object.polarity_scores(comment)
    
    # Append the compound score to the polarity list
    polarity.append(sentiment_dict['compound'])

    return polarity


# Initialize lists to store polarity and categorized comments
polarity = []
positive_comments = []
negative_comments = []
neutral_comments = []

# Open the file ytcomments.txt in read mode with utf-8 encoding
with open("ytcomments.txt", 'r', encoding='utf-8') as f:
    comments = f.readlines()

# Print a message indicating the start of sentiment analysis
print("Analyzing Comments...")

# Loop through the comments and analyze their sentiment
for index, comment in enumerate(comments):
    # Analyze each comment's sentiment and update polarity list
    polarity = sentiment_scores(comment, polarity)

    # Categorize the comments based on compound score
    if polarity[-1] > 0.05:
        positive_comments.append(comment)
    elif polarity[-1] < -0.05:
        negative_comments.append(comment)
    else:
        neutral_comments.append(comment)

# Print the first 5 polarity scores to verify
print("Polarity scores:", polarity[:5])

# Calculate the average polarity score
avg_polarity = sum(polarity) / len(polarity)

# Print the average polarity score
print("Average Polarity:", avg_polarity)

# Categorize the video response based on average polarity
if avg_polarity > 0.05:
    print("The Video has got a Positive response")
elif avg_polarity < -0.05:
    print("The Video has got a Negative response")
else:
    print("The Video has got a Neutral response")

# Find and print the most positive comment
most_positive_comment = comments[polarity.index(max(polarity))]
print("The comment with most positive sentiment:", most_positive_comment.strip(), 
      "with score", max(polarity), 
      "and length", len(most_positive_comment))

# Find and print the most negative comment
most_negative_comment = comments[polarity.index(min(polarity))]
print("The comment with most negative sentiment:", most_negative_comment.strip(), 
      "with score", min(polarity), 
      "and length", len(most_negative_comment))

# Count of positive, negative, and neutral comments
positive_count = len(positive_comments)
negative_count = len(negative_comments)
neutral_count = len(neutral_comments)

# Labels and data for the Bar chart
labels = ['Positive', 'Negative', 'Neutral']
comment_counts = [positive_count, negative_count, neutral_count]

# Creating the bar chart
plt.bar(labels, comment_counts, color=['blue', 'red', 'grey'])

# Adding labels and title to the plot
plt.xlabel('Sentiment')
plt.ylabel('Comment Count')
plt.title('Sentiment Analysis of Comments')

# Display the chart
plt.show()

# Labels and data for the Pie chart
labels = ['Positive', 'Negative', 'Neutral']
comment_counts = [positive_count, negative_count, neutral_count]

# Setting the size of the figure
plt.figure(figsize=(10, 6))  # 10 inches wide and 6 inches in height

# Plotting the pie chart
plt.pie(comment_counts, labels=labels, autopct='%1.1f%%', startangle=90)

# Ensuring the pie chart is a circle
plt.axis('equal')

# Displaying the pie chart
plt.show()