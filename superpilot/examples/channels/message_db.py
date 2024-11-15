
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MongoDB:
    def __init__(self):
        # MongoDB connection setup
        self.client = MongoClient("mongodb://localhost:27017/")  # Use your MongoDB URI if needed
        self.db = self.client["messages_db"]  # Database name
        self.collection = self.db["messages"]  # Collection name

    def get_collection(self):
        return self.collection

# Create a MongoDB instance
mongo_db_instance = MongoDB()