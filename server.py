import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import datetime
# import flask
from flask import Flask, request, redirect
# import our custom db interfact
import db
from db import Event, Image, Participant, User, Study
# Jinja2 templating
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates', encoding='utf-8-sig'))

app = Flask(__name__, static_folder="images") # change to non static in future

dateformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")
datetimeformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
timeformat = lambda x: datetime.datetime.strptime(x, "%H:%M:%S")

db_session = db.get_session()

# db.create_db(and_add_images=True)
@app.route("/")
def hello():
	template = env.get_template('index.html')
	return template.render(
		studies=Study.query.all(),
		participants=Participant.query.all(),
		users=User.query.all(),
		num_images=len(Image.query.all()),
		sql_text=open('create_db.txt','r').read()
		).encode('utf-8')

@app.route("/reboot_db")
def create():
	db.read_log() # clear the log
	db.drop_db()
	drop_sql = db.read_log()
	db_session = db.create_db()
	sql = db.read_log()
	with open('create_db.txt','w') as f:
			f.write(sql)
	return "<h2>Rebooted DB</h2><h3>Drop SQL:</h3><pre>"+drop_sql+"</pre><h3>Create SQL:</h3><pre>"+sql+"</pre>"

@app.route("/images")
def images():
	res = "<h1>All Images</h1>\n"
	for image in Image.query.all():
		res += "<img src='/%s' href='/%s'>" % (image.thumnail_url, image.full_url)
		res += " : ".join([str.strip(str(x)) for x in image]) + "<br>\n"
	return res

@app.route("/user/<int:user_id>")
def user(user_id):
	res = "<h2> User: " + str(user_id) + "</h2>\n"
	res += "<h4> User has access to the following studies: </h4>\n"
	for study in User.query.filter(user_id=user_id).studies:
		res += " : ".join([str.strip(str(x)) for x in study]) + "<br>\n"
	return res

@app.route("/study/<int:study_id>")
def study(study_id):
	template = env.get_template('study.html')
	study = Study.query.filter(Study.study_id==study_id).one()
	study_participants = study.participants
	participants_to_add = [x for x in Participant.query.all() if not x in study_participants]

	return template.render(
		study_id=study_id,
		study_name=study.name,
		participants=study_participants,
		participants_to_add=participants_to_add,
		).encode('utf-8')

@app.route("/participant/<int:participant_id>")
def participant(participant_id):
	daterange = None
	if "date_min" in request.args.keys() and "date_max" in request.args.keys():
		date_min = request.args.get('date_min', default=None, type=datetimeformat)
		date_max = request.args.get('date_max', default=None, type=datetimeformat)
		print date_min, date_max
		daterange={'min':date_min,'max':date_max}
	# if date_min is not None and date_max is not None:
	# 	date_min = dateutil.parser.parse(date_min)
	# 	date_max = dateutil.parser.parse(date_max)

	template = env.get_template('participant.html')
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	if daterange is None:
		images = participant.images[0:100]
	else:
		images = participant.images.filter(Image.time<daterange.max and Image.time>daterange.min)[0:100]
		# images = db.get_images(participant_id=participant_id, date_range=daterange)
	# days = db.get_participant_days(participant_id)
	return template.render(
		name=participant.name,
		images=participant.images,
		# images=images[0:100],
		days=[],
		daterange=daterange
		)

@app.route("/participant/<int:participant_id>/<int:event_id>")
def event(participant_id, event_id):
	template = env.get_template('participant.html')

	images = Image.query.filter(Image.participant_id==participant_id, Image.event_id==event_id)
	return template.render(
		name=Participant.query.filter(Participant.participant_id==participant_id).one().name,
		num_images=db.get_images(participant_id=participant_id, only_number=True, event_id=event_id),
		images=images[0:100],
		daterange=daterange
		)

@app.route("/add_studyparticipant", methods=["POST"])
def add_studyparticipant():
	study_id, participant_id = request.form['study_id'], request.form['participant_id']
	study = Study.query.filter(Study.study_id==study_id).one()
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	if study and participant:
		participant.studies.append(study)		
		return redirect("/study/" + study_id)
	return "Method = " + request.method + " study_id : " + str(study_id) + " participant_id : " + str(participant_id)

@app.route("/remove_studyparticipant", methods=["POST"])
def remove_studyparticipant():
	study_id, participant_id = request.form['study_id'], request.form['participant_id']
	study = Study.query.filter(Study.study_id==study_id).one()
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	if study and participant:
		if study in participant.studies:
			participant.studies.remove(study)	
			return redirect("/study/" + study_id)
		else:
			return "participant not in that study"
	return "Method = " + request.method + " study_id : " + str(study_id) + " participant_id : " + str(participant_id)



@app.route("/create_event", methods=["POST"])
def create_event():
	start_time = request.form['study_id'], request.form['participant_id']

@app.errorhandler(500)
def internal_server_error(error):
	return "Error 500: " + str(error)

if __name__ == "__main__":
	print "running on port 5000"
	app.run(debug=True)
