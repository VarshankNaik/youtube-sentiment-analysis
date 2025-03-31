from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
import torch
import re
import requests
from collections import defaultdict
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

app = Flask(__name__)
CORS(app)

# ✅ Corrected Model Path
local_model_path = "C:/PROJECT_FINAL/PROJECT/sentiment_model2"
API_KEY = "AIzaSyBtJjniAVMDaQN3OaocZpP7MyAVBgXPl2Q"

# ✅ Check if model exists before loading
if not os.path.exists(local_model_path):
    raise FileNotFoundError(f"Model directory not found: {local_model_path}")

tokenizer = DistilBertTokenizer.from_pretrained(local_model_path, local_files_only=True)
model = DistilBertForSequenceClassification.from_pretrained(local_model_path, local_files_only=True).to("cuda" if torch.cuda.is_available() else "cpu")
model.eval()

# ✅ Extract Video ID from URL
def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

# ✅ Fetch Video & Channel Details
def fetch_video_details(video_id):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={API_KEY}"
    response = requests.get(url).json()
    
    if "items" not in response or not response["items"]:
        return None

    video_data = response["items"][0]["snippet"]
    stats = response["items"][0]["statistics"]
    
    return {
        "title": video_data["title"],
        "channel_title": video_data["channelTitle"],
        "description": video_data["description"],
        "published_at": video_data["publishedAt"],
        "views": stats.get("viewCount", 0),
        "likes": stats.get("likeCount", 0),
        "comments": stats.get("commentCount", 0),
    }

# ✅ Fetch Comments
def fetch_comments(video_id, max_comments=100):
    comments = []
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={API_KEY}&maxResults={max_comments}"
    response = requests.get(url).json()

    for item in response.get("items", []):
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(comment)

    return comments

# ✅ Predict Sentiment
def predict_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=512)
    inputs = {key: val.to("cuda" if torch.cuda.is_available() else "cpu") for key, val in inputs.items()}
                                                                                
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=1).item()
    
    return {0: "Negative", 1: "Neutral", 2: "Positive"}[predicted_class]

# ✅ Feature Keywords
feature_keywords = {
    "camera": ["camera", "photo", "picture", "selfie", "lens"],
    "battery": ["battery", "charging", "power", "backup", "fast charge"],
    "performance": ["performance", "speed", "lag", "processor", "gaming"],
    "display": ["screen", "display", "resolution", "brightness", "refresh rate"]
}

# ✅ Feature Extraction Function
def extract_features(comment):
    comment = comment.lower()
    feature_counts = {feature: 0 for feature in feature_keywords}

    for feature, keywords in feature_keywords.items():
        if any(keyword in comment for keyword in keywords):
            feature_counts[feature] = 1  # Feature is mentioned in the comment

    return feature_counts

# ✅ API Endpoint
@app.route("/analyze", methods=["POST"])
def analyze_youtube():
    data = request.json
    youtube_url = data.get("url")
    
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    video_details = fetch_video_details(video_id)
    comments = fetch_comments(video_id)

    if not comments:
        return jsonify({"error": "No comments found", "total_comments": 0}), 404

    # ✅ Convert comments to DataFrame
    df = pd.DataFrame(comments, columns=["comment"])
    df["sentiment"] = df["comment"].apply(predict_sentiment)

    # ✅ Extract features
    df_features = df["comment"].apply(extract_features).apply(pd.Series)

    # ✅ Ensure all feature columns exist
    for feature in feature_keywords.keys():
        if feature not in df_features.columns:
            df_features[feature] = 0

    # ✅ Merge extracted features back into DataFrame
    df = pd.concat([df, df_features], axis=1)

    # ✅ Sentiment Summary
    sentiment_counts = df["sentiment"].value_counts().to_dict()
    sentiment_counts = {
        "Positive": sentiment_counts.get("Positive", 0),
        "Neutral": sentiment_counts.get("Neutral", 0),
        "Negative": sentiment_counts.get("Negative", 0)
    }

    # ✅ Feature Analysis
    feature_scores = defaultdict(int)
    for _, row in df.iterrows():
        sentiment = row["sentiment"]
        for feature in feature_keywords.keys():
            if row[feature] == 1:  # Feature is mentioned in the comment
                if sentiment == "Positive":
                    feature_scores[feature] += 1  # Add 1 for positive sentiment
                elif sentiment == "Negative":
                    feature_scores[feature] -= 1  # Subtract 1 for negative sentiment

    response_data = {
        "video_details": video_details,
        "sentiment_summary": sentiment_counts,
        "feature_analysis": dict(feature_scores),
        "total_comments": len(comments),  # ✅ Fixed total comments count
        "comments": df.to_dict(orient="records")
    }

    return jsonify(response_data)

# ✅ Run Flask Server
if __name__ == "__main__":
    app.run(debug=True)
