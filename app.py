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

# Define a set of predefined options for the "notes" field
STANCE_OPTIONS = ["Agree", "Disagree"]

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

from bson import ObjectId

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
        # Calculate the new comment ID
        new_comment_id = 1 if not article.get("comments") else article["comments"][-1]["id"] + 1

        # Create a new comment
        new_comment = {
            "id": new_comment_id,
            "username": request.form["username"],
            "comment": request.form["comment"],
            "stance": request.form.getlist("stance"),
            "date": request.form["date"]
        }
        
        # Validate that the selected notes are from the predefined set
        for stance in new_comment["stance"]:
            if stance not in STANCE_OPTIONS:
                return make_response(jsonify({"error": f"Invalid stance: {stance}"}), 400)

        # Update the article with the new comment
        valid_data.update_one({"_id": obj_id}, {"$push": {"comments": new_comment}})

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
        # Find the comment by commentID
        comment = next((c for c in article.get("comments", []) if c["id"] == commentID), None)

        if comment:
            # Remove the comment from the article's comments array
            valid_data.update_one({"_id": obj_id}, {"$pull": {"comments": {"id": commentID}}})
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
            # Update the comment fields
            comment["username"] = request.form["username"]
            comment["comment"] = request.form["comment"]
            comment["stance"] = request.form["stance"]

            # Update the article with the modified comment
            valid_data.update_one({"_id": obj_id, "comments.id": commentID}, {"$set": {"comments.$": comment}})
            
            return make_response(jsonify(comment), 200)
        else:
            return make_response(jsonify({"error": "Comment not found"}), 404)
    else:
        return make_response(jsonify({"error": "Article not found"}), 404)


if __name__ == "__main__":
    app.run( debug = True )
    
    