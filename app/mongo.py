import pymongo
import pymongo.collation
from django.conf import settings
from bson import ObjectId
import time

class MongoDatabase(object):
        def __init__(self): 
                self.client = pymongo.MongoClient(settings.MONGO_DATABASE_HOST)
                self.DATABASE = self.client[settings.MONGO_DATABASE_NAME]
                
        def find(self, collection, query):
            return self.DATABASE[collection].find(query)

        def find_one(self, collection, query):
            return self.DATABASE[collection].find_one(query)

        def aggregate(self, collection, query):
            return self.DATABASE[collection].aggregate(query)

        def find_one_and_update(self, collection, id, fieldArray, username, companyid): 
            return self.DATABASE[collection].find_one_and_update(
                {'_id' : ObjectId(id) }, {"$set": fieldArray })
            
        def insert(self, collection,fieldArray): 
            x = self.DATABASE[collection].insert_one(fieldArray)
            return x

class BaseDBObject(object):     
        def __init__(self):    
                self.created = round(time.time() * 1000)
                self.modified = round(time.time() * 1000)
                self.deleted = False
                self.updated = False
       
        
class data_wrapper(BaseDBObject):
        def __init__(self, group_id, data):
                self.group_id = group_id
                self.data = data
                BaseDBObject.__init__(self)
