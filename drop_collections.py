from pymongo import MongoClient

def clear_all_collections(database_name, connection_string="mongodb://127.0.0.1:27017"):
    client = MongoClient(connection_string)
    db = client[database_name]

    # Get a list of all collection names in the database
    collections = db.list_collection_names()

    # Drop each collection
    for collection_name in collections:
        db[collection_name].drop()

    print("All collections dropped from the database.")

# Replace "your_database_name" with the actual name of your database
clear_all_collections("your_database_name")