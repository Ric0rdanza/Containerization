from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS

import psycopg2

import jwt

secret = "random_string"

app = Flask(__name__)
CORS(app)
api = Api(app)

parser = reqparse.RequestParser()

parser.add_argument("username", location = "form")
parser.add_argument("password", location = "form")

def encode(json):
    token = jwt.encode(json, secret, algorithm = "HS256")
    return token

def decode(token):
    try:
        json = jwt.decode(token, secret, algorithms = ["HS256"])
    except:
        json = {}
    finally:
        return json

def db_signup(username, password):
    conn = psycopg2.connect(database="postgresdb", user="postgresadmin", password="zxcZXC123", host="10.106.44.03")
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username = %s", (username,))
    data = cur.fetchone()
    if data is None:
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            conn.close()
            return True
        except:
            conn.rollback()
    conn.close()
    return False

def db_signin(username, password):
    conn = psycopg2.connect(database="postgresdb", user="postgresadmin", password="zxcZXC123", host="10.106.44.03")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    data = cur.fetchone()
    if data is None:
        return False
    return True

def db_verify(username, password):
    conn = psycopg2.connect(database="postgresdb", user="postgresadmin", password="zxcZXC123", host="10.106.44.03")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    data = cur.fetchone()
    if data is None:
        return False
    return True

class CORS_Resource(Resource):
    def options(self):
        return {'Allow': '*'}, 200, {'Access-Control-Allow-Origin': '*',
                                     'Access-Control-Allow-Methods': 'HEAD, OPTIONS, GET, POST, DELETE, PUT',
                                     'Access-Control-Allow-Headers': 'Content-Type, Content-Length, Authorization, Accept, X-Requested-With , yourHeaderFeild',
                                     }

class Signup(CORS_Resource):
    def post(self):
        args = parser.parse_args()
        print(args)
        if not args["username"] or not args["password"]:
            return "error", 403
        if db_signup(args["username"], args["password"]) == False:
            return "Username already exists", 200
        return 200

class Login(Resource):
    def post(self):
        args = parser.parse_args()
        if not args["username"] or not args["password"]:
            return "error", 403
        if db_signin(args["username"], args["password"]):
            return encode(args), 200
        return "incorrect username or password", 401

# Used to check correctness of token
class Status(Resource):
    def post(self):
        token = ""
        print(request.headers)
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(' ')[1]
        args = decode(token)
        if "username" not in args:
            return "", 403
        if db_verify(args["username"], args["password"]):
            return args["username"], 200
        return "", 401
    
api.add_resource(Signup, '/users')
api.add_resource(Login, '/users/login')
api.add_resource(Status, '/verify')

if __name__ == "__main__":
    app.run()
