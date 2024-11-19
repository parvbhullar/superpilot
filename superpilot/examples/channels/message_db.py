
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")  
        self.db = self.client["messages_db"] 
        self.collection = self.db["messages"]  
    def get_collection(self):
        return self.collection

# DB instance
mongo_db_instance = MongoDB()