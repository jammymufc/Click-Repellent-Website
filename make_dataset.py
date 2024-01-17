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

        # Extract speaker's name from the filename
        speaker_name = filename.split('_')[0].replace('-', ' ')  # Adjust the split logic based on your filename format

        # Open the image file in binary mode
        with open(file_path, 'rb') as f:
            # Insert the image binary data into GridFS
            file_id = fs.put(f.read(), filename=filename)

            # Insert metadata along with the file_id into the image collection
            image_collection.insert_one({
                'filename': filename,
                'file_id': file_id,
                'speaker_name': speaker_name
            })

    print(f"Images loaded from {folder_path} to {collection} with speaker names")

def add_speakers_collection():
    # Connect to MongoDB
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client.clickRepellent

    # Create a new collection for speakers
    speakers_collection = db.speakers

    # Get distinct speaker names from the speaker_images collection
    distinct_speaker_names = db.valid.distinct('speaker')

    # Loop through each distinct speaker name
    for speaker in distinct_speaker_names:
        # Retrieve statements associated with the speaker from the valid collection
        speaker_statements = list(db.valid.find({'speaker': speaker}, {'statement': 1, 'label': 1}))

        # Initialize label counts
        label_counts = {'barely-true': 0, 'false': 0, 'half-true': 0, 'mostly-true': 0, 'pants-fire': 0}

        # Initialize job title and party affiliation
        job_title = ''
        party_affiliation = ''

        # Find job title and party affiliation from the speaker_info collection
        speaker_info = db.valid.find_one({'speaker': speaker})
        if speaker_info:
            job_title = speaker_info.get('speaker_job_title', '')
            party_affiliation = speaker_info.get('party_affiliation', '')
            
        # Update label counts based on statements
        for statement in speaker_statements:
            label = statement.get('label')
            if label in label_counts:
                label_counts[label] += 1
        
        print(f"Speaker: {speaker}, Label Counts: {label_counts}")

        # Insert speaker data into the speakers collection
        speakers_collection.insert_one({
            'speaker_name': speaker,
            'statements': speaker_statements,
            'job_title': job_title,
            'party_affiliation': party_affiliation,
            'label_counts': label_counts
        })

    print("Speakers collection updated with speaker data")
    
def create_political_figures():
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client.clickRepellent

    # Load valid data
    political_figures = db.political_figures   
    with open('new_people_details_w_images.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        political_figures.insert_many(data)
    print("Political Figures loaded")


#if __name__ == "__main__":
    # Specify the folder path containing PNG images
    #images_folder_path = 'C:\\Users\\USER\\Documents\\YEAR 4 UNI\\Computing Project\\Click Repellent Website\\Speaker_charts'

    # Specify the name of the collection to store images
    #images_collection_name = 'speaker_images'

    #insert_images_to_collection(images_collection_name, images_folder_path)


def insert_subjectcharts_to_collection(collection, folder_path):
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

        # Extract speaker's name from the filename
        subject_name = filename.split('_')[0].replace('-', ' ')  

        # Open the image file in binary mode
        with open(file_path, 'rb') as f:
            # Insert the image binary data into GridFS
            file_id = fs.put(f.read(), filename=filename)

            # Construct the URL for the image
            image_url = f"/assets/subject_charts/{filename}"

            # Insert metadata along with the file_id and image_url into the image collection
            image_collection.insert_one({
                'filename': filename,
                'file_id': file_id,
                'subject_name': subject_name,
                'image_url': image_url
            })

    print(f"Images loaded from {folder_path} to {collection} with speaker names and URLs")

if __name__ == "__main__":
    # Specify the folder path containing PNG images
    images_folder_path = 'C:\\Users\\USER\\Documents\\YEAR 4 UNI\\Computing Project\\Click Repellent Website\\Subject_charts'

    # Specify the name of the collection to store images
    images_collection_name = 'subject_charts'

    insert_subjectcharts_to_collection("subject_charts", "C:\\Users\\USER\\Documents\\YEAR 4 UNI\\Computing Project\\Click Repellent Back-End\\Subject_charts")

#create_database()
#insert_images_to_collection()
#add_speakers_collection()
#create_political_figures()
