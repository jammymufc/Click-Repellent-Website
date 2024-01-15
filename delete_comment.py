from pymongo import MongoClient
from bson import ObjectId

client = MongoClient( "mongodb://127.0.0.1:27017" )
db = client.clickRepellent 
users_collection = db.users
article_collection = db.valid

# Specify user and comment ObjectId values
user_id = ObjectId("659c1f069a8e1d3106645775")
comment_id = ObjectId("65a5423765002577a81e3e92")

# Update the user document to remove the specific comment
""" users_collection.update_one(
    {'_id': user_id},
    {'$pull': {'comments': {'id': comment_id}}}
) """

users_collection.update_one(
    {'_id': user_id},
    {'$pull': {'scraped_articles': {'_id': comment_id}}}
    
)



