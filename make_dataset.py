from pymongo import MongoClient
import json

def create_database():
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client.clickRepellent

    # Load train data
    train_data = db.train    
    with open('train.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        train_data.insert_many(data)
    print("Training Data loaded")

    # Load test data
    test_data = db.test   
    with open('test.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        test_data.insert_many(data)
    print("Test Data loaded")
    
    # Load valid data
    valid_data = db.valid   
    with open('valid.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        valid_data.insert_many(data)
    print("Valid Data loaded")

create_database()
