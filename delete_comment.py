from pymongo import MongoClient
from bson import ObjectId

client = MongoClient( "mongodb://127.0.0.1:27017" )
db = client.clickRepellent 
users_collection = db.users
article_collection = db.valid

# Specify user and comment ObjectId values
user_id = ObjectId("659c0f687030e18f51d442a8")
comment_id = ObjectId("659c37705d7a5bb4518de3e8")

# Update the user document to remove the specific comment
""" users_collection.update_one(
    {'_id': user_id},
    {'$pull': {'comments': {'id': comment_id}}}
) """

article_collection.update_one(
    {'_id': user_id},
    {'$pull': {'comments': {'id': comment_id}}}
)


