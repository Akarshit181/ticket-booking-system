from pymongo import MongoClient

from app.utils.config import settings

class MongoDB:
    client = None
    db = None 
    
    @classmethod
    def connect(cls):
        if cls.client is None:
            cls.client = MongoClient(settings.mongo_uri)
            cls.db = cls.client[settings.database_name]
            print("MongoDB Connected")

    @classmethod
    def get_db(cls):
        return cls.db
        