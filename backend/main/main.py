from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS

import requests
import re
import random
import sys
import base62

import psycopg2

app = Flask(__name__)
CORS(app)
api = Api(app)

def db_connect():
	conn = psycopg2.connect(database="postgresdb", user="postgresadmin", password="zxcZXC123", host="10.106.44.03")
	return conn

def db_exists_shorturl(shorturl):
	conn = db_connect()
	cur = conn.cursor()
	cur.execute("SELECT * FROM urls WHERE shorturl = \'%s\'" % (shorturl))
	if cur.rowcount == 0:
		conn.close()
		return False
	conn.close()
	return True

def get_shorturl(long_url):  
	random.seed(10)
	num = random.randint(0, sys.maxsize)
	short_url = base62.encode(num)
	while db_exists_shorturl(short_url):
		num = random.randint(0, sys.maxsize)
		short_url = base62.encode(num)
	return short_url 

# database structure:
# urls: {originalurl pk, shorturl}
# ownership: {username, shorturl}

def db_create_shorturl(username, originalurl, shorturl):
	conn = db_connect()
	cur = conn.cursor()
	cur.execute("SELECT * FROM urls WHERE originalurl = \'%s\'" % (originalurl))
	if cur.rowcount == 0:
		cur.execute("INSERT INTO urls (originalurl, shorturl) VALUES (\'%s\', \'%s\')" % (originalurl, shorturl))
		cur.execute("INSERT INTO ownership (username, shorturl) VALUES (\'%s\', \'%s\')" % (username, shorturl))
		conn.commit()
		conn.close()
		return shorturl
	shorturl = cur.fetchone()[1]
	cur.execute("SELECT * FROM ownership WHERE username = \'%s\' AND shorturl = \'%s\'" % (username, shorturl))
	if cur.rowcount == 0:
		cur.execute("INSERT INTO ownership (username, shorturl) VALUES (\'%s\', \'%s\')" % (username, shorturl))
		conn.commit()
		conn.close()
		return shorturl
	else:
		conn.close()
		return shorturl

def db_delete_shorturl(username, shorturl):
	conn = db_connect()
	cur = conn.cursor()
	cur.execute("SELECT * FROM ownership WHERE username = \'%s\' AND shorturl = \'%s\'" % (username, shorturl))
	if cur.rowcount == 0:
		conn.close()
		return False
	cur.execute("DELETE FROM ownership WHERE username = \'%s\' AND shorturl = \'%s\'" % (username, shorturl))
	cur.execute("SELECT * FROM ownership WHERE shorturl = \'%s\'" % (shorturl))
	if cur.rowcount == 0:
		cur.execute("DELETE FROM urls WHERE shorturl = \'%s\'" % (shorturl))
	conn.commit()
	conn.close()
	return True

def db_get_originalurl(shorturl):
	conn = db_connect()
	cur = conn.cursor()
	cur.execute("SELECT * FROM urls WHERE shorturl = \'%s\'" % (shorturl))
	if cur.rowcount == 0:
		conn.close()
		return ""
	originalurl = cur.fetchone()[0]
	conn.close()
	return originalurl

def db_get_all_url_map(username):
	conn = db_connect()
	cur = conn.cursor()
	cur.execute("SELECT originalurl, urls.shorturl FROM ownership, urls WHERE ownership.username = \'%s\' AND ownership.shorturl = urls.shorturl" % (username))
	if cur.rowcount == 0:
		conn.close()
		return {}
	url_map = {}
	for row in cur:
		url_map[row[0]] = row[1]
	conn.close()
	return url_map

def db_delete_all_url_map(username):
	conn = db_connect()
	cur = conn.cursor()
	cur.execute("SELECT shorturl FROM ownership WHERE username = \'%s\'" % (username))
	if cur.rowcount == 0:
		conn.close()
		return False
	shorturl_list = []
	for row in cur:
		shorturl_list.append(row[0])
	cur.execute("DELETE FROM ownership WHERE username = \'%s\'" % (username))
	conn.commit()
	cur = conn.cursor()
	for shorturl in shorturl_list:
		cur.execute("SELECT * FROM ownership WHERE shorturl = \'%s\'" % (shorturl))
		if cur.rowcount == 0:
			cur.execute("DELETE FROM urls WHERE shorturl = \'%s\'" % (shorturl))
	conn.commit()
	conn.close()
	return True

parser = reqparse.RequestParser()

parser.add_argument("url", location = "form")

def is_url(candidate):
	schema = ["http", "https", "ftp"]
	mark = "://"
	if mark not in candidate:
		return False
	search_obj = re.search("(.*)://(.*)", candidate, re.M|re.I)
	if search_obj.group(1) not in schema:
		return False
	if search_obj.group(2)[:-1] == ".":
		return False
	if "." not in search_obj.group(2):
		return False
	return True

# Send a request to login server to varify that token is correct
def is_token_valid(token):
	data = {"Authorization": token}
	username = requests.post("http://10.106.44.01:5001/verify", headers = data)
	if username.status_code == 200:
		uid = username.text
		return uid
	else:
		return False

def get_uid(request):
	token = ""
	if "Authorization" in request.headers:
		token = request.headers["Authorization"]
	else:
		return "forbidden", 403
	uid = is_token_valid(token)
	if not uid:
		return "forbidden", 403
	return uid, 200

class WithId(Resource):
	# e.g. 127.0.0.1:5000/<shortened url>
	# Retrieve original url from short url given
	def get(self, id):
		originalurl = db_get_originalurl(id)
		if originalurl == "":
			return "error", 404
		return originalurl, 200

	# Delete a shortened url
	def delete(self, id):
		# check the correctness of the token
		uid, status = get_uid(request)
		if status != 200:
			return uid, status
		if db_delete_shorturl(uid, id) == False:
			return "error", 404
		return '', 204

class WithoutId(Resource):
	# e.g. 127.0.0.1:5000/
	# Retrieve all url map of user
	def get(self):
		uid, status = get_uid(request)
		if status != 200:
			return uid, status
		result = db_get_all_url_map(uid)
		return result, 200

	# Create shortened url
	def post(self):
		args = parser.parse_args()
		# verify the token
		uid, status = get_uid(request)
		if status != 200:
			return uid, status
		# check correctness of given url
		if not is_url(args['url']):
			return "error", 400
			
		short_url = get_shorturl(args['url'])
		short_url = db_create_shorturl(uid, args['url'], short_url)

		return short_url, 201
	# Delete all mapping of a user
	def delete(self):
		uid, status = get_uid(request)
		if status != 200:
			return uid, status
		if db_delete_all_url_map(uid) == False:
			return "error", 404
		return "", 204

class Test(Resource):
	def get(self):
		return map_url, 200
# flask route
api.add_resource(WithoutId, '/')
api.add_resource(WithId, '/<id>')

api.add_resource(Test, '/test')

if __name__ == "__main__":
	app.run(debug = True)
