from pymongo import MongoClient, ReturnDocument

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.clickRepellent
valid_data = db.valid

for valid in valid_data.find():
    agree_count = len(valid.get("comments", []))
    valid_data.update_one(
        {"_id": valid["_id"]},
        {"$set": {"agree_count": agree_count}},
    )

for valid in valid_data.find():
    disagree_count = len(valid.get("comments", []))
    valid_data.update_one(
        {"_id": valid["_id"]},
        {"$set": {"disagree_count": disagree_count}},
    )