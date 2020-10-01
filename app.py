
# flask imports 
from flask import Flask, request, jsonify, make_response 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm.attributes import flag_modified
import uuid # for public id 
from  werkzeug.security import generate_password_hash, check_password_hash 
# imports for PyJWT authentication 
import jwt 
from datetime import datetime, timedelta 
from functools import wraps 
from flask_cors import CORS
# creates Flask object 
app = Flask(__name__) 
# configuration 
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE 
# INSTEAD CREATE A .env FILE AND STORE IN IT 
app.config['SECRET_KEY'] = 'your secret key'
# database name 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# creates SQLALCHEMY object 
db = SQLAlchemy(app) 
CORS(app)
# Database ORMs 
class User(db.Model): 
    id = db.Column(db.Integer, primary_key = True) 
    public_id = db.Column(db.String(50), unique = True) 
    name = db.Column(db.String(100)) 
    phone = db.Column(db.String(70), unique = True) 
    password = db.Column(db.String(80))

class ProfileUser(db.Model):
    id_profile = db.Column(db.Integer, primary_key = True)
    id_user = db.Column(db.String(50), unique = True)
    level = db.Column(db.Integer)
    point = db.Column(db.Integer)
    current_turn = db.Column(db.Integer)

class GameHistory(db.Model):
    id_match = db.Column(db.Integer, primary_key = True)
    id_user = db.Column(db.String(50))
    id_opponent = db.Column(db.String(50))
    match_status = db.Column(db.Integer)
    date_time = db.Column(db.String(50))
   
# decorator for verifying the JWT 
def token_required(f): 
    @wraps(f) 
    def decorated(*args, **kwargs): 
        token = None
        # jwt is passed in the request header 
        if 'x-access-token' in request.headers: 
            token = request.headers['x-access-token'] 
        # return 401 if token is not passed 
        if not token: 
            return jsonify({'message' : 'Token is missing !!'}), 401
   
        try: 
            # decoding the payload to fetch the stored details 
            data = jwt.decode(token, app.config['SECRET_KEY']) 
            current_user = User.query\
                .filter_by(public_id = data['public_id'])\
                .first() 
        except: 
            return jsonify({ 
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes 
        return  f(current_user, *args, **kwargs) 
   
    return decorated 

def get_user_by_token(token):
    try: 
        # decoding the payload to fetch the stored details 
        data = jwt.decode(token, app.config['SECRET_KEY']) 
        current_user = User.query\
            .filter_by(public_id = data['public_id'])\
            .first() 
    except: 
        return None
    # returns the current logged in users contex to the routes 
    return  current_user

# this route sends back list of users users 
@app.route('/game_history', methods =['GET']) 
@token_required
def get_game_histories(current_user): 
    game_histories = db.engine.execute( "SELECT game_history.id_user, game_history.id_opponent, game_history.match_status, game_history.date_time FROM game_history where game_history.id_user="\
        +str(current_user.id) +" or game_history.id_opponent="+str(current_user.id))

    output = [] 
    for game_history in game_histories:
        # appending the user data json  
        # to the response list 
        output.append({ 
            'id_user': game_history[0], 
            'id_opponent' : game_history[1],
            'match_status' : game_history[2],
            'date_time' : game_history[3],
        }) 
    print(output)
    return jsonify({'game_histories': output}) 

# User Database Route 
# this route sends back list of users users 
@app.route('/ranking', methods =['GET']) 
@token_required
def get_all_users(current_user): 
    
    #users = User.query.order_by().all() 
    users = db.engine.execute(
        "SELECT user.phone, user.name, profile_user.point FROM user, profile_user WHERE user.id = profile_user.id_user ORDER BY profile_user.point DESC")
    # converting the query objects 
    # to list of jsons 
    output = [] 
    for user in users:
        # appending the user data json  
        # to the response list 
        output.append({ 
            'phone': user[0], 
            'name' : user[1],
            'point' : user[2] 
        }) 
    print(output)
    return jsonify({'users': output}) 
   
# route for loging user in 
@app.route('/login', methods =['POST']) 
def login(): 
    # creates dictionary of form data 
    auth = request.form 
    print(auth)
    
    if not auth or not auth.get('phone') or not auth.get('password'): 
        # returns 401 if any phone or / and password is missing 
        return make_response( 
            'Could not verify', 
            401, 
            {'WWW-Authenticate' : 'Basic realm ="Login required !!"'} 
        ) 
   
    user = User.query\
        .filter_by(phone = auth.get('phone'))\
        .first() 
    
    if not user: 
        # returns 401 if user does not exist 
        return make_response( 
            'Could not verify', 
            401, 
            {'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'} 
        ) 
   
    if check_password_hash(user.password, auth.get('password')): 
        # generates the JWT Token 
        token = jwt.encode({ 
            'public_id': user.public_id, 
            'exp' : datetime.utcnow() + timedelta(minutes = 120) 
        }, app.config['SECRET_KEY']) 
   
        return make_response(jsonify({'token' : token.decode('UTF-8'), 'name':user.name}), 201) 
    # returns 403 if password is wrong 
    return make_response( 
        'Could not verify', 
        403, 
        {'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'} 
    ) 
   
# signup route
@app.route('/signup', methods =['POST']) 
def signup(): 
    # creates a dictionary of the form data 
    data = request.form 
    print('=>> ', data)
    print('->>', request.form)
    # gets name, phone and password 
    name, phone = data.get('name'), data.get('phone') 
    password = data.get('password') 
   
    # checking for existing user 
    user = User.query.filter_by(phone = phone).first() 
    if not user: 
        # database ORM object 
        user = User( 
            public_id = str(uuid.uuid4()), 
            name = name, 
            phone = phone, 
            password = generate_password_hash(password) 
        ) 

        
        # insert user 
        db.session.add(user) 
        db.session.commit() 
        
        profileUser = ProfileUser( 
            id_user = user.id, 
            level = 1, 
            point = 0, 
            current_turn = 20
        ) 
        # insert user 
        db.session.add(profileUser) 
        db.session.commit()

        #return make_response('Successfully registered.', 201)
        token = jwt.encode({ 
            'public_id': user.public_id, 
            'exp' : datetime.utcnow() + timedelta(minutes = 120) 
        }, app.config['SECRET_KEY'])
        return make_response(jsonify({'token' : token.decode('UTF-8'), 'name':user.name}), 201)
    else: 
        # returns 202 if user already exists 
        return make_response('User already exists. Please Log in.', 202) 
   
@app.route('/ranking_user', methods =['GET']) 
@token_required
def get_user_rank(current_user): 
    
    #users = User.query.order_by().all() 
    users = db.engine.execute(
        "SELECT user.phone, user.name, profile_user.point FROM user, profile_user WHERE user.id = profile_user.id_user ORDER BY profile_user.point DESC")
    # converting the query objects 
    # to list of jsons 
    output = [] 
    d = 0
    for user in users:
        d = d+1
        if user[0] == current_user.phone:
            return jsonify({ 
            'phone': user[0], 
            'name': user[1], 
            'rank' : d,
            'point' : user[2] 
        }) 
    
    return make_response('User doesn\'t exist', 400) 
    
@app.route('/turn_user', methods =['GET']) 
@token_required
def get_user_turn(current_user): 
    
    #users = User.query.order_by().all() 
    users = db.engine.execute(
        "SELECT profile_user.current_turn FROM profile_user WHERE profile_user.id_user =" +str(current_user.id)) 
    
    turn_users = [{'turn': x[0]} for x in users]
    if len(turn_users) <= 0:
       return make_response('User doesn\'t exist', 400) 

    return jsonify({'turn_user': turn_users[0]})

@app.route('/end_game', methods =['POST']) 

@token_required
def save_game_history(current_user):
    data = request.form

    token1, token2 = data.get('token1'), data.get('token2') 
    start_time = data.get('start_time')
    result1, result2 = data.get('result1'), data.get('result2') 
    user1, user2 = get_user_by_token(token1), get_user_by_token(token2)

    profileUser1 = ProfileUser.query.filter_by(id_user=user1.id).first()
    profileUser2 = ProfileUser.query.filter_by(id_user=user2.id).first()
    current_turn1 = profileUser1.current_turn - 1
    current_turn2 = profileUser2.current_turn - 1
    profileUser1.current_turn = current_turn1
    profileUser2.current_turn = current_turn2

    # flag_modified(profileUser, "current_turn")
    # db.session.merge(profileUser)


    status = 0
    if result1 > result2:
        profileUser1.point+=3
        status = 1
    elif result1 < result2:
        status = -1
        profileUser2.point+=3

    

    gameHistory = GameHistory( 
        id_user = user1.id, 
        id_opponent = user2.id, 
        match_status = status, 
        date_time = start_time
    ) 

    # insert gameHistory 
    db.session.add(gameHistory) 
    db.session.commit()

    return make_response("Update sucessfully.", 200)


if __name__ == "__main__": 
    # setting debug to True enables hot reload 
    # and also provides a debuger shell 
    # if you hit an error while running the server 
    app.run(host="192.168.1.104",debug = True) 
    #app.run(debug = True) 
    