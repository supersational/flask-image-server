# import flask
from flask import Flask, request, redirect
# import our custom db interfact
import db
# Jinja2 templating
from jinja2 import Environment, FileSystemLoader
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
env = Environment(loader=FileSystemLoader('templates', encoding='utf-8-sig'))

app = Flask(__name__, static_folder="images") # change to non static in future
import codecs

# db.create_db(and_add_images=True)
@app.route("/")
def hello():
	template = env.get_template('index.html')
	participants = []
	for p in db.get_participants():
		participants.append({
			'name': p.name,
			'participant_id':p.participant_id,
			'num_studies': len(db.get_studyparticipants(participant_id=p.participant_id))
			})

	studies = []
	for s in db.get_studies():
		studies.append({
			'name': s.name,
			'study_id':s.study_id,
			'num_participants': len(db.get_participants(study_id=s.study_id))
			})

	return template.render(
		studies=studies,
		participants=participants,
		users=db.get_users(),
		num_images=db.get_images(only_number=True),
		sql_text=open('create_db.txt','r').read()
		).encode('utf-8')

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

@app.route("/user/<int:user_id>")
def user(user_id):
	res = "<h2> User: " + str(user_id) + "</h2>\n"
	res += "<h4> User has access to the following studies: </h4>\n"
	for study in db.get_user_studies(user_id):
		res += " : ".join([str.strip(str(x)) for x in study]) + "<br>\n"
	return res

@app.route("/study/<int:study_id>")
def study(study_id):
	template = env.get_template('study.html')
	study_participants = db.get_participants(study_id=study_id)
	participants_to_add = [x for x in db.get_participants() if not x in study_participants]

	return template.render(
		study_id=study_id,
		study_name=db.get_studies(study_id=study_id)[0].name,
		participants=study_participants,
		participants_to_add=participants_to_add,
		).encode('utf-8')

@app.route("/participant/<int:participant_id>")
def participant(participant_id):
	template = env.get_template('participant.html')
	images = db.get_images(participant_id=participant_id)
	return template.render(
		name=db.get_participants(participant_id=participant_id)[0].name,
		num_images=len(images),
		images=images[0:100]
		)

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
	print "running on port 5000"
	app.run(debug=True)
