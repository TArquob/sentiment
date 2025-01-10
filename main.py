import os
import time
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType
import firebase_admin
from firebase_admin import credentials, db

# Step 1: Set Up Firebase
cred = credentials.Certificate("fb.json")  # Path to your Firebase credentials
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://sentiment-1e078-default-rtdb.firebaseio.com/"  # Replace with your database URL
})
# Function to send results to Firebase (used later in the driver program)
def send_to_firebase(text, sentiment):
    ref = db.reference("sentiment_analysis")
    ref.push({
        "text": text,
        "sentiment": sentiment,
        "timestamp": time.time()
    })

# Step 2: Load Pretrained Lightweight Model (DistilBERT)
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Function for sentiment classification using DistilBERT
def classify_sentiment(text):
    if not text:
        return "neutral"
    tokens = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    outputs = model(**tokens)
    predictions = outputs.logits.argmax(dim=-1).item()
    return "positive" if predictions == 1 else "negative"

# Register the function as a UDF for PySpark
sentiment_udf = udf(classify_sentiment, StringType())

# Step 3: Initialize SparkSession
spark = SparkSession.builder \
    .appName("Streaming Sentiment Analysis with Firebase and Console Output") \
    .getOrCreate()

# Step 4: Streaming Data Source
streaming_df = spark.readStream \
    .format("text") \
    .load("social_stream/") \
    .withColumnRenamed("value", "text")

# Step 5: Apply Sentiment Classification
processed_stream = streaming_df \
    .withColumn("sentiment", sentiment_udf(col("text")))

# Step 6: Collect Results and Send to Firebase
def write_to_firebase(batch_df, batch_id):
    # Collect data from the batch as a Pandas DataFrame
    results = batch_df.select("text", "sentiment").toPandas()
    for _, row in results.iterrows():
        # Print the result to the terminal
        print(f"Text: {row['text']}, Sentiment: {row['sentiment']}")
        
        # Send the result to Firebase
        send_to_firebase(row["text"], row["sentiment"])

# Start the Streaming Query
query = processed_stream.writeStream \
    .outputMode("update") \
    .foreachBatch(write_to_firebase) \
    .start()

# Simulate Streaming Posts
posts = [
    "This is amazing! I absolutely love it.",
    "i hate fruits"
]

streaming_folder = "social_stream/"
if not os.path.exists(streaming_folder):
    os.mkdir(streaming_folder)

# Simulate new posts arriving over time
for i, post in enumerate(posts):
    with open(f"{streaming_folder}/post_{i}.txt", "w") as f:
        f.write(post)
    time.sleep(2)  # Simulate a 2-second interval between posts

# Wait for the query to finish
query.awaitTermination()
sentiment-1e078-default-rtdb.firebaseio.com
