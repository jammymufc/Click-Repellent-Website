from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['clickRepellent']  # Replace 'your_database_name' with your actual database name


# Drop the speaker_images collection
db['speaker_images'].drop()
db['speaker_images.chunks'].drop()
db['speaker_images.files'].drop()