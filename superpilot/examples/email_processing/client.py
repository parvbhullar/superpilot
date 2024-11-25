import pymongo

def create_mongo_client():
    """Create and return a MongoDB client instance."""
    client = pymongo.MongoClient('mongodb://localhost:27017/')  
    db = client['email_db']  
    collection = db['emails'] 
    return collection

def store_email(subject, sender, snippet, body, date):
    """Store email data in MongoDB."""
    collection = create_mongo_client()
    
    email_data = {
        'subject': subject,
        'sender': sender,
        'snippet': snippet,
        'body': body,
        'date': date,
        'read': False
    }
    
    result = collection.insert_one(email_data)

    print(f"Email stored in MongoDB with ID: {result.inserted_id}")
