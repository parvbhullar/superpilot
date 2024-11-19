import logging
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.memory import ChatMemoryBuffer
from datetime import datetime
from message_db import mongo_db_instance

class DocumentManager:
    @staticmethod
    def load_documents():
        bulk_messages = list(mongo_db_instance.get_collection().find())
        documents = []

        for msg in bulk_messages:
            if 'content' in msg and isinstance(msg['content'], str):
                author_name = 'Unknown'
                if isinstance(msg.get('author'), dict):
                    author_name = msg['author'].get('name', 'Unknown')
                elif isinstance(msg.get('author'), str): 
                    author_name = msg['author']
                
                documents.append(Document(
                    text=msg['content'],
                    metadata={
                        'author': author_name,
                        'timestamp': msg.get('timestamp', ''),
                        'channel_id': msg.get('channel_id', '')
                    }
                ))

        if not documents:
            logging.warning("No documents found in MongoDB. The chat engine might not respond effectively.")
        
        return documents

class ChatEngineManager:
    def __init__(self):
        self.index = None
        self.memory = None
        self.chat_engine = None

    def initialize_chat_engine(self, documents):
        self.index = VectorStoreIndex.from_documents(documents)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

        self.chat_engine = self.index.as_chat_engine(
            chat_mode="context",
            memory=self.memory,
            system_prompt=(
                "You are a chatbot that can have normal interactions and discuss various topics. "
                "You should also utilize historical Discord messages for context."
            ),
        )

    def get_response(self, message_content):
        return self.chat_engine.chat(message_content)

class DatabaseHandler:
    @staticmethod
    def store_message_in_db(user_message, bot_response, author, channel_id):
        try:
            collection = mongo_db_instance.get_collection()
            document = {
                'content': user_message,
                'response': bot_response,
                'author': author,
                'channel_id': channel_id,
                'timestamp': str(datetime.now()) 
            }
            collection.insert_one(document)  
            logging.info(f"Stored message and response for author {author} in channel {channel_id}")
        except Exception as e:
            logging.error(f"Error storing message in MongoDB: {e}")
