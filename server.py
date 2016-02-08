# import flask
from flask import Flask, request, redirect
# import our custom db interfact
import db

app = Flask(__name__, static_folder="images") # change to non static in future

# db.create_db(and_add_images=True)
@app.route("/")
def hello():
	try:
		res = "<h2>Control Panel:</h2>\n"
		# for sp in db.get_studyparticipants():
		# 	res += " : ".join([str.strip(str(x)) for x in sp]) + "<br>"
 
		res += "<h3>Studies:</h3>\n"
		for study in db.get_studies():
			res += "<a href='/study/%s'>" % (study.study_id,)  
			res += " : ".join([str.strip(str(x)) for x in study])
			res += "</a> (" + str(len(db.get_studyparticipants(study_id=study.study_id))) + " participants) <br>\n"

		res += "<h3>Participants:</h3>\n"
		for participant in db.get_participants():
			res += "<a href='/participant/%s'>" % (participant.participant_id, )  
			res += " : ".join([str.strip(str(x)) for x in participant])
			res += "</a> (in " + str(len(db.get_studyparticipants(participant_id=participant.participant_id))) + " studies)<br>\n"

		res += "<h3>Users:</h3>\n"
		for user in db.get_users():
			res += "<a href='/users/%s'>" % (user.user_id,)  
			res += " : ".join([str.strip(str(x)) for x in user]) 
			res += "</a><br>\n"
		res += "<br>\n<br>\n<a href='/reboot_db'><button>reboot DB</button></a>"
		n = db.get_images(only_number=True)
		print n
		res += "<p>there are " + str(n) + " images in the db</p>"
		with open('create_db.txt','r') as f:
			res += "<textarea style='position:absolute; right:3px; top:3px' rows='50' cols='100'>"
			res += f.read()
			res += "</textarea>"
		return res 
	except Exception as e:
		return str(e)

@app.route("/reboot_db")
def create():
	res = db.create_db(and_add_images=True)
	res = "<h2>Rebooted DB</h2><p>"+ ";</p><p>\n".join(res.split(";")) + "</p"
	return res

@app.route("/images")
def images():
	res = "<h1>All Images</h1>\n"
	for image in db.get_images():
		res += "<img src='/%s' href='/%s'>" % (image.thumnail_url, image.full_url)
		res += " : ".join([str.strip(str(x)) for x in image]) + "<br>\n"
	return res

@app.route("/users/<int:user_id>")
def user(user_id):
	res = "<h2> User: " + str(user_id) + "</h2>\n"
	res += "<h4> User has access to the following studies: </h4>\n"
	for study in db.get_user_studies(user_id):
		res += " : ".join([str.strip(str(x)) for x in study]) + "<br>\n"
	return res

@app.route("/study/<int:study_id>")
def study(study_id):
	res = "<h2> Study: " + str(study_id) + ", " + db.get_studies(study_id=study_id)[0].name + "</h2>\n" 
	study_participants = db.get_participants(study_id=study_id)
	for participant in study_participants:
		res += "<a href='/participant/%s'>" % (participant.participant_id,)  
		res += " : ".join([str.strip(str(x)) for x in participant])
		res += "</a>"
		res += "<form action='/remove_studyparticipant' method='POST'> "
		res += "<input type='hidden' name='study_id' value='%s'> " % (study_id, )
		res += "<input type='hidden' name='participant_id' value='%s'> " % (participant.participant_id, )
		res += "<input type='submit' value='Delete'> "
		res += "</form><br>\n"

	res += "<form action='/add_studyparticipant' method='POST'> "
	res += "<p>add a participant to this study: </p>\n<select name='participant_id'>\n"
	for participant in db.get_participants():
		if participant not in study_participants:
			res += "<option value='%s'>%s</option>" % (participant.participant_id, participant.name)  
	res += "</select>"
	res += "<input name='study_id' style='display:none' value='%s'> " % (study_id, )
	res += "<input type='submit' value='Add'> "
	res += "</form> "
	return res

@app.route("/participant/<int:participant_id>")
def participant(participant_id):
	res = "<h2> Participant: " + str(participant_id) + "</h2>\n"
	for image in db.get_images(participant_id):
		res += "<a href='/%s'><img src='/%s' ></a>" % (image.full_url, image.thumbnail_url)
		res += "<p>" + " : ".join([str.strip(str(x)) for x in image]) + "</p><br>\n"
	return res

@app.route("/add_studyparticipant", methods=["POST"])
def modify_studyparticipant():
	study_id, participant_id = request.form['study_id'], request.form['participant_id']
	
	if int(study_id) % 1 == 0 and int(participant_id) % 1 == 0:
		db.add_studyparticipant(study_id, participant_id)
		return redirect("/study/" + study_id)
	return "Method = " + request.method + " study_id : " + str(study_id) + " participant_id : " + str(participant_id)

@app.route("/remove_studyparticipant", methods=["POST"])
def add_studyparticipant():
	study_id, participant_id = request.form['study_id'], request.form['participant_id']

	if int(study_id) % 1 == 0 and int(participant_id) % 1 == 0:
		db.remove_studyparticipant(study_id, participant_id)
		return redirect("/study/" + study_id)

	return "Method = " + request.method + " study_id : " + str(study_id) + " participant_id : " + str(participant_id)

@app.errorhandler(500)
def internal_server_error(error):
	return "Error 500: " + str(error)

if __name__ == "__main__":
	print "started"
	app.run(debug=True)
	print "started"
