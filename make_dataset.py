from pymongo import MongoClient
import json
import gridfs
import os

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
    
def insert_images_to_collection(collection, folder_path):
    # Connect to MongoDB
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client.clickRepellent

    # Create a new collection for images
    image_collection = db[collection]

    # Initialize GridFS for storing binary data
    fs = gridfs.GridFS(db, collection=collection)

    # Loop through the files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Open the image file in binary mode
        with open(file_path, 'rb') as f:
            # Insert the image binary data into GridFS
            file_id = fs.put(f.read(), filename=filename)

            # Insert metadata along with the file_id into the image collection
            image_collection.insert_one({
                'filename': filename,
                'file_id': file_id
            })

    print(f"Images loaded from {folder_path} to {collection}")

if __name__ == "__main__":
    # Specify the folder path containing PNG images
    images_folder_path = 'C:\\Users\\USER\\Documents\\YEAR 4 UNI\\Computing Project\\Click Repellent Website\\Speaker_charts'

    # Specify the name of the collection to store images
    images_collection_name = 'speaker_images'

    insert_images_to_collection(images_collection_name, images_folder_path)

#create_database()
#insert_images_to_collection()

