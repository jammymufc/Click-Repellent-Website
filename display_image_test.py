from pymongo import MongoClient
from gridfs import GridFS
import matplotlib.pyplot as plt
from PIL import Image
import io

def display_image_from_collection(collection_name):
    # Connect to MongoDB
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client.clickRepellent

    # Access the specified collection
    image_collection = db[collection_name]

    # Initialize GridFS
    fs = GridFS(db, collection=collection_name)

    # Query the first document in the collection
    document = image_collection.find_one()

    if document:
        # Retrieve the file_id from the document
        file_id = document['file_id']

        # Retrieve the image binary data from GridFS
        image_data = fs.get(file_id).read()

        # Convert binary data to an image
        image = Image.open(io.BytesIO(image_data))

        # Display the image using matplotlib
        plt.imshow(image)
        plt.title(document['filename'])
        plt.show()
    else:
        print("No images found in the collection.")

if __name__ == "__main__":
    # Specify the name of the collection containing images
    images_collection_name = 'speaker_images'

    # Display an image from the collection
    display_image_from_collection(images_collection_name)
