# import flask
from flask import Flask
import db
app = Flask(__name__)

print db.get_all_participants()
print db.get_all_users()
res = str(" ".join(map(str,db.get_all_participants())))
print res
db.add_images()

@app.route("/")
def hello():
	try:
		res = "<h1>Participants</h1>\n"
		for participant in db.get_all_participants():
			res += " : ".join([str.strip(str(x)) for x in participant]) + "<br>\n"
		res += "<h1>Users</h1>\n"
		for user in db.get_all_users():
			res += "<a href='/users/%s'>" % (user[0],)  
			res += " : ".join([str.strip(str(x)) for x in user]) + "<br>\n"
		res += "<br>\n<br>\n<a href='/create'><button>reboot DB</button></a>"
		return res 
	except Exception as e:
		return str(e)

@app.route("/create")
def create():
	db.create_db()
	return "success"

@app.route("/users/<int:user_id>")
def user(user_id):
	res = "<h2> User: " + str(user_id) + "</h2>\n"
	res += "<h4> User has access to the following studies: </h4>\n"
	for study in db.get_user_studies(user_id):
		res += " : ".join([str.strip(str(x)) for x in study]) + "<br>\n"
	return res

@app.errorhandler(500)
def internal_server_error(error):
	return "Error 500: " + str(error)

if __name__ == "__main__":
    app.run()