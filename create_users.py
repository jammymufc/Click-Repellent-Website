from pymongo import MongoClient
import bcrypt

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.clickRepellent      # select the database
users = db.users        # select the collection name

user_list = [
          { 
            "name" : "Jamie Maguire",
            "username" : "jamie",  
            "password" : b"jamie_m",
            "email" : "maguire-j44@ulster.ac.uk",
            "admin" : True
          },
          { 
            "name" : "Marge Simpson",
            "username" : "marge",  
            "password" : b"marge_s",
            "email" : "marge@springfield.net",
            "admin" : False
          },
          { 
            "name" : "Homer Simpson",
            "username" : "homer",  
            "password" : b"homer_s",
            "email" : "homer@springfield.net",
            "admin" : True
          }
       ]

for new_user in user_list:
      new_user["password"] = bcrypt.hashpw(new_user["password"], bcrypt.gensalt())
      users.insert_one(new_user)
