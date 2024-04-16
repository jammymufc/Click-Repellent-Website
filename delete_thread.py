from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.clickRepellent
users = db.users

def delete_user_thread(username):
    # Find the user document by username
    user = users.find_one({'username': username})

    # If user exists and has a thread, delete the thread from the user document
    if user and 'thread' in user:
        users.update_one({'username': username}, {'$unset': {'thread': ""}})
        print(f"Thread deleted for user '{username}'.")
    else:
        print(f"No thread found for user '{username}'.")

# Call the function to delete the thread for user 'homer'
delete_user_thread('homer')
