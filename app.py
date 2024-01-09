from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
import jwt
import datetime
from functools import wraps
import bcrypt 

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecret'

client = MongoClient( "mongodb://127.0.0.1:27017" )
db = client.clickRepellent 
train_data = db.train
test_data = db.test
valid_data = db.valid
blacklist = db.blacklist
users = db.users

# Define a set of predefined options for the "notes" field
STANCE_OPTIONS = ["Agree", "Disagree"]

def convert_objectid_to_string(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [convert_objectid_to_string(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_string(value) for key, value in obj.items()}
    else:
        return obj

def jwt_required(func):
    @wraps(func)
    def jwt_required_wrapper(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # Include the algorithm parameter to specify the decoding algorithm
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        
        bl_token = blacklist.find_one( { "token" : token } )
        if bl_token is not None:
            return make_response( jsonify( { 'message' : 'Token has been cancelled' } ), 401)
        return func(*args, **kwargs)
    return jwt_required_wrapper

def admin_required(func): 
    @wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        token = request.headers['x-access-token']
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401

        if data.get("admin"):
            return func(*args, **kwargs)
        else:
            return make_response(jsonify({'message': 'Admin access required'}), 401)
        
    return admin_required_wrapper

@app.route("/api/v1.0/articles", methods=["GET"])
def show_all_articles():
    page_num, page_size = 1, 10
    if request.args.get("pn"):
        page_num = int(request.args.get('pn'))
    if request.args.get("ps"):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))
    
    data_to_return = []
    for article in valid_data.find().skip(page_start).limit(page_size):
        article["_id"] = str(article["_id"])
        
        data_to_return.append(article)
    
    return make_response( jsonify( data_to_return ), 200 )

@app.route("/api/v1.0/articles/<string:id>", methods=["GET"])
def show_one_article(id):
    article = valid_data.find_one( { "_id" : ObjectId(id) } )
    if article is not None:
        article["_id"] = str(article["_id"])
        
        return make_response( jsonify( article ), 200 )
    else:
        return make_response( jsonify( { "error" : "Invalid Article ID" } ), 404)

@app.route("/api/v1.0/articles/<string:id>/comments", methods=["POST"])
def add_new_comment(id):
    try:
        # Convert the id to ObjectId
        obj_id = ObjectId(id)
    except:
        return make_response(jsonify({"error": "Invalid Article ID format"}), 400)

    # Find the article by ObjectId
    article = valid_data.find_one({"_id": obj_id})

    if article:
        # Check if the user has already commented
        username = request.form["username"]
        if any(comment["username"] == username for comment in article.get("comments", [])):
            return make_response(jsonify({"error": "User has already commented on this article"}), 400)

        # Calculate the new comment ID
        new_comment_id = 1 if not article.get("comments") else article["comments"][-1]["id"] + 1

        # Create a new comment
        new_comment = {
            "id": new_comment_id,
            "username": username,
            "comment": request.form["comment"],
            "stance": request.form.getlist("stance"),
            "date": request.form["date"]
        }

        # Validate that the selected stances are from the predefined set
        for stance in new_comment["stance"]:
            if stance not in STANCE_OPTIONS:
                return make_response(jsonify({"error": f"Invalid stance: {stance}"}), 400)

        # Update the article with the new comment
        valid_data.update_one(
            {"_id": obj_id},
            {
                "$push": {"comments": new_comment},
                "$inc": {"comment_count": 1}  # Increment the comment_count field
            }
        )

        # Initialize counts for each stance in the article if not present
        for stance in STANCE_OPTIONS:
            valid_data.update_one(
                {"_id": obj_id, f"{stance.lower()}_count": {"$exists": False}},
                {"$set": {f"{stance.lower()}_count": 0}}
            )

        # Increment the counts for each stance in the article
        for stance in new_comment["stance"]:
            valid_data.update_one(
                {"_id": obj_id},
                {"$inc": {f"{stance.lower()}_count": 1}}
            )
        

        return make_response(jsonify(new_comment), 201)
    else:
        return make_response(jsonify({"error": "Article not found"}), 404)


    
@app.route("/api/v1.0/articles/<string:id>/comments/<int:commentID>", methods=["GET"])
def fetch_one_comment(id, commentID):
    try:
        # Convert the id to ObjectId
        obj_id = ObjectId(id)
    except:
        return make_response(jsonify({"error": "Invalid Article ID format"}), 400)

    # Find the article by ObjectId
    article = valid_data.find_one({"_id": obj_id})

    if article:
        # Find the comment by commentID
        comment = next((c for c in article.get("comments", []) if c["id"] == commentID), None)

        if comment:
            return make_response(jsonify(comment), 200)
        else:
            return make_response(jsonify({"error": "Comment not found"}), 404)
    else:
        return make_response(jsonify({"error": "Article not found"}), 404)

@app.route("/api/v1.0/articles/<string:id>/comments", methods=["GET"])
def fetch_all_comments(id):
    try:
        # Convert the id to ObjectId
        obj_id = ObjectId(id)
    except:
        return make_response(jsonify({"error": "Invalid Article ID format"}), 400)

    # Find the article by ObjectId
    article = valid_data.find_one({"_id": obj_id})

    if article:
        comments = article.get("comments", [])
        return make_response(jsonify(comments), 200)
    else:
        return make_response(jsonify({"error": "Article not found"}), 404)

@app.route("/api/v1.0/articles/<string:id>/comments/<int:commentID>", methods=["DELETE"])
def delete_comment(id, commentID):
    try:
        # Convert the id to ObjectId
        obj_id = ObjectId(id)
    except:
        return make_response(jsonify({"error": "Invalid Article ID format"}), 400)

    # Find the article by ObjectId
    article = valid_data.find_one({"_id": obj_id})

    if article:
        # Find the comment by ID
        comment = next((comment for comment in article.get("comments", []) if comment["id"] == commentID), None)

        if comment:
            # Decrement the comment_count field
            valid_data.update_one({"_id": obj_id}, {"$inc": {"comment_count": -1}})

            # Decrement the counts for each stance in the article
            for stance in comment["stance"]:
                valid_data.update_one(
                    {"_id": obj_id},
                    {"$inc": {f"{stance.lower()}_count": -1}}
                )

            # Remove the comment from the comments list
            valid_data.update_one({"_id": obj_id}, {"$pull": {"comments": {"id": commentID}}})

            # Remove the comment from the user's comments
            users.update_one(
                {"username": comment["username"]},
                {"$pull": {"comments": {"id": commentID}}}
            )

            return make_response(jsonify({}), 204)
        else:
            return make_response(jsonify({"error": "Comment not found"}), 404)
    else:
        return make_response(jsonify({"error": "Article not found"}), 404)

    
@app.route("/api/v1.0/articles/<string:id>/comments/<int:commentID>", methods=["PUT"])
def edit_comment(id, commentID):
    try:
        # Convert the id to ObjectId
        obj_id = ObjectId(id)
    except:
        return make_response(jsonify({"error": "Invalid Article ID format"}), 400)

    # Find the article by ObjectId
    article = valid_data.find_one({"_id": obj_id})

    if article:
        # Find the comment by commentID
        comment = next((c for c in article.get("comments", []) if c["id"] == commentID), None)

        if comment:
            # Decrement counts for the old stances
            for stance in comment["stance"]:
                valid_data.update_one(
                    {"_id": obj_id},
                    {"$inc": {f"{stance.lower()}_count": -1}}
                )

            # Update the comment fields
            comment["username"] = request.form["username"]
            comment["comment"] = request.form["comment"]
            comment["stance"] = request.form.getlist("stance")

            # Validate that the selected stances are from the predefined set
            for stance in comment["stance"]:
                if stance not in STANCE_OPTIONS:
                    return make_response(jsonify({"error": f"Invalid stance: {stance}"}), 400)

            # Increment counts for the new stances
            for stance in comment["stance"]:
                valid_data.update_one(
                    {"_id": obj_id},
                    {"$inc": {f"{stance.lower()}_count": 1}}
                )

            # Update the article with the modified comment
            valid_data.update_one({"_id": obj_id, "comments.id": commentID}, {"$set": {"comments.$": comment}})
            
            return make_response(jsonify(comment), 200)
        else:
            return make_response(jsonify({"error": "Comment not found"}), 404)
    else:
        return make_response(jsonify({"error": "Article not found"}), 404)



@app.route("/api/v1.0/login", methods=["GET"])
def login():
    auth = request.authorization
    if auth:
        user = users.find_one( { "username" : auth.username } )
        if user is not None:
            if bcrypt.checkpw( bytes( auth.password, 'UTF-8' ), user["password"] ):
                print(f"Provided password: {auth.password}")
                token = jwt.encode( {
                    '_id': str(user["_id"]),
                    'name': user["name"],
                    'username': user["username"],
                    'email': user["email"],
                    'admin': user["admin"],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=90)
                    }, app.config['SECRET_KEY'])
                return make_response(jsonify( { 'token' : token}), 200 )
            else:
                return make_response( jsonify( { 'message' : 'Enter a valid password'} ), 401)
        else:
            return make_response( jsonify( { 'message' : 'Enter a valid username'} ), 401)
    
    return make_response( jsonify( { 'message' : 'Authentication required' } ), 401 )

@app.route("/api/v1.0/logout", methods=['GET'])
@jwt_required
def logout():
    token = request.headers['x-access-token']
    blacklist.insert_one( { "token" : token } )
    return make_response( jsonify( { 'message' : 'Logout successful' } ), 200)


@app.route("/api/v1.0/createaccount", methods = ["POST"])
def add_new_user():
    if "name" in request.form and "password" in request.form and "email" in request.form and "username" in request.form:
        
        # Check if the username or email already exists
        existing_user = users.find_one(
            {
                "$or": [
                    {"username": request.form["username"]},
                    {"email": request.form["email"]},
                ]
            }
        )

        if existing_user:
            return make_response(
                jsonify({"error": "Username or email already exists"}), 409
            )
        
        
        new_user = {
            "name" : request.form["name"],
            "password" : bcrypt.hashpw(request.form["password"].encode('utf8'), bcrypt.gensalt()),
            "email" : request.form["email"],
            "username" : request.form["username"],
            "admin" : False
        }
        
        new_user_id = users.insert_one(new_user)
        new_user_link = "http://localhost:5000/api/v1.0/users/" + \
            str(new_user_id.inserted_id)
        return make_response( jsonify( { "url" : new_user_link } ), 201 )
    else:
        return make_response( jsonify ( { "error" : "Missing Form Data" } ), 404 )
    
@app.route("/api/v1.0/users", methods=["GET"])
def fetch_all_users():
    all_users = list(users.find({}))

    # Convert ObjectId to string for JSON serialization
    all_users = [convert_objectid_to_string(user) for user in all_users]

    # Convert bytes to string for JSON serialization
    for user in all_users:
        # Only decode if password is bytes
        if 'password' in user and isinstance(user['password'], bytes):
            try:
                user['password'] = user['password'].decode('utf-8')
            except UnicodeDecodeError:
                # Handle the case where decoding fails
                user['password'] = "Password decoding error"

    if all_users:
        return make_response(jsonify(all_users), 200)
    else:
        return make_response(jsonify({"message": "No users found"}), 404)


@app.route("/api/v1.0/users/<string:id>", methods=["GET"])
def fetch_one_user(id):
    user = users.find_one({"_id": ObjectId(id)})

    if user is not None:
        # Convert ObjectId to string for serialization
        user = convert_objectid_to_string(user)

        # Convert Binary field to base64-encoded string
        #only decode if password is bytes
        if 'password' in user and isinstance(user['password'], bytes):
            user['password'] = user['password'].decode('utf-8') if 'password' in user else None

        return make_response(jsonify(user), 200)
    else:
        return make_response(jsonify({"error": "Invalid User ID"}), 404)
    
@app.route("/api/v1.0/users/<string:id>", methods = ["DELETE"])
def delete_user(id):

    result = users.delete_one( { "_id" : ObjectId(id) } )
    if result.deleted_count == 1:
        return make_response( jsonify ( {} ), 204 )
    else:
        return make_response( jsonify( { "error" : "Invalid User ID" } ), 404 )
    
@app.route("/api/v1.0/users/<string:id>/comments", methods=["GET"])
def fetch_all_user_comments(id):
    data_to_return = []
    user = users.find_one(
        { "_id" : ObjectId(id) }, { "comments" : 1, "_id" : 0 }
    )
    
    if user and "comments" in user:
        for comment in user["comments"]:
            comment["_id"] = str(comment["_id"])
            data_to_return.append(comment)
        
        return make_response( jsonify( data_to_return ), 200 )
    else:
        return make_response( jsonify( { "error" : "No comments found" } ), 404)
    
    
@app.route("/api/v1.0/users/<string:id>/articles/<string:article_id>/read", methods=["POST"])
def add_to_read(id, article_id):
    
    # Check if the user ID and article ID are valid
    if not ObjectId.is_valid(id) or not ObjectId.is_valid(article_id):
        return make_response(jsonify({"error": "Invalid user or article ID"}), 400)
    
    article = valid_data.find_one({"_id": ObjectId(article_id)})
    user = users.find_one({"_id": ObjectId(id)})
    
    new_read = {
        "_id": ObjectId(article_id),
        "article_name": article['statement'],
        "label": article['label'],
        "date_added": datetime.datetime.utcnow()
    }
    
    existing_read_article = next((r for r in user.get("read_articles", []) if r.get("_id") == new_read["_id"]), None)
    
    if existing_read_article:
        # If the article exists, don't add
        return make_response(jsonify({"error": "Article has already been read."}), 401)
    else:
        users.update_one(
            {"_id": ObjectId(id)},
            {
                "$push": {"read_articles": new_read}
            }
        )
        
        valid_data.update_one(
            {"_id": ObjectId(article_id)},
            {
                "$inc": {"read_count": 1}
            }
        )
        
        new_read_link = "http://localhost:5000/api/v1.0/users/" + id + \
            "/read/" + str(article_id)
        return make_response(jsonify({"url": new_read_link}), 201)


@app.route("/api/v1.0/users/<string:user_id>/read/<string:article_id>", methods=["DELETE"])
def delete_read_article(user_id, article_id):
    user = users.find_one({"_id": ObjectId(user_id)})

    if user is None:
        return make_response(jsonify({"error": "Invalid User ID"}), 404)

    # Check if the article is in the user's "read_articles" list
    article_to_delete = next((entry for entry in user.get("read_articles", []) if str(entry.get("_id")) == article_id), None)

    if article_to_delete is None:
        return make_response(jsonify({"error": "Article not found in tried list"}), 404)

    # Delete the beer entry from the user's "tried_and_tested" list
    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"read_articles": {"_id": article_to_delete["_id"]}}}
    )

    return make_response(jsonify({"message": "Article deleted from read list"}), 204)

if __name__ == "__main__":
    app.run( debug = True )
    
    