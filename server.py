# date handling
import datetime
dateformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")
datetimeformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
timeformat = lambda x: datetime.datetime.strptime(x, "%H:%M:%S")
# import flask
from flask import Flask, request, redirect, send_from_directory, url_for
from flask import render_template
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
# flask setup
app = Flask(__name__, static_folder='static', template_folder='templates')
login_manager = LoginManager()
login_manager.init_app(app)
# import our custom db interfact
import db
from db import Event, Image, Participant, User, Study, Schema, Label, Folder
db_session = db.get_session()

# Add Jinja2 filters
@app.template_filter('time')
def get_time(s):
	if type(s) == str:
	    return s[11:20]
	elif s is None:
		return ""
	else:
		return s.strftime("%H:%M:%S")

@app.template_filter('verbose_seconds')
def verbose_seconds(seconds):
	days, rem = divmod(seconds, 86400)
	hours, rem = divmod(rem, 3600)
	minutes, seconds = divmod(rem, 60)
	if minutes + hours + days <= 0 and seconds < 1: seconds = 1
	locals_ = locals()
	magnitudes_str = ("{n} {magnitude}".format(n=int(locals_[magnitude]), magnitude=magnitude)
			            for magnitude in ("days", "hours", "minutes", "seconds") if locals_[magnitude])
	return ", ".join(magnitudes_str)

# Login handling
@login_manager.user_loader
def load_user(id):
	return User.query.get(int(id))


login_manager.login_view = 'login'
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')

	username = request.form['username']
	password = request.form['password']
	print username, password
	registered_user = User.query.filter_by(username=username).first()

	if registered_user is None:
		return render_template('login.html', message="error: incorrect username")
	elif registered_user.password != password:
		return render_template('login.html', message="error: incorrect password")
	elif login_user(registered_user, remember=True):
		return redirect('/')
	else:
		return render_template('login.html', message="error: in login_user")

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect('/')

@login_manager.unauthorized_handler
def unauthorized():
	return render_template('login.html', message="This page requires login!")

@app.route("/")
def index():
	return render_template('index.html',
		studies=Study.query.all(),
		participants=Participant.query.all(),
		users=User.query.all(),
		num_images=len(Image.query.all()),
		sql_create=open('create_db.txt','r').read(),
		sql_text=db.read_log()
		)

# Custom static data
@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images', filename)

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
@login_required
def images():
	res = "<h1>All Images</h1>\n"
	for image in Image.query.all():
		res += "<img src='%s' href='%s'>" % (image.thumbnail_url, image.full_url)
		# res += " : ".join([str.strip(str(x)) for x in image]) + "<br>\n"
	return res

@app.route("/user/<int:user_id>")
def user(user_id):
	user = User.query.filter(User.user_id==user_id).one()
	res = "<h2> User: " + user.username + " (" + str(user_id) + ")</h2>\n"
	res += "<h4> User has access to the following studies: </h4>\n"
	for study in user.studies:
		res += "Study: %s, id: %s, has %s participants %s <br>\n" % (study.name, study.study_id, len(study.participants), dir(study))
	return res

@app.route("/study/<int:study_id>")
def study(study_id):
	study = Study.query.filter(Study.study_id==study_id).one()
	study_participants = study.participants
	participants_to_add = [x for x in Participant.query.all() if not x in study_participants]
	return render_template('study.html', 
		study_id=study_id,
		study_name=study.name,
		participants=study_participants,
		participants_to_add=participants_to_add,
		sql_text=db.read_log()[:2000]
		)

@app.route("/participant/<int:participant_id>")
def participant(participant_id):
	daterange = None
	if "date_min" in request.args.keys() and "date_max" in request.args.keys():
		date_min = request.args.get('date_min', default=None, type=datetimeformat)
		date_max = request.args.get('date_max', default=None, type=datetimeformat)
		print date_min, date_max
		daterange={'min':date_min,'max':date_max}

	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	if daterange is None:
		images = participant.images
	else:
		images = [img for img in participant.images if img.image_time<daterange['max'] and img.image_time > daterange['min']]
	images = sorted(images, key=lambda x: x.image_time)[0:100]
	# print "sorted list:"
	# for img in images
	# 	print img, '' if not daterange else str(img.image_time > daterange['max']) + str(img.image_time < daterange['min'])
	return render_template('participant.html', 
		name=participant.name,
		id=participant.participant_id,
		images=images[:100],
		days=participant.get_images_by_hour(),
		daterange=daterange,
		num_images=len(participant.images),
		sql_text=db.read_log()[:2000],
		schema=Schema.query.first()
		)

@app.route("/participant/<int:participant_id>/<int:event_id>")
def event(participant_id, event_id):
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	event = Event.query.filter(Event.event_id==event_id, Event.participant_id==participant_id).one()
	images = sorted(event.images, key=lambda x: x.image_time)

	daterange={'min':event.start_time,'max':event.end_time}
	return render_template('participant.html', 
		name=participant.name,
		id=participant.participant_id,
		images=images[0:100],
		days=participant.get_images_by_hour(),
		daterange=daterange,
		num_images=len(event.images),
		prev_event_id=getattr(event.prev_event, 'event_id', None), # None as default if no prev_event exists
		next_event_id=getattr(event.next_event, 'event_id', None),
		prev_image=event.prev_image,
		next_image=event.next_image,
		event_id=event.event_id,
		event_seconds=event.length.total_seconds(),
		sql_text=db.read_log(),
		schema=Schema.query.first()
		)

@app.route("/participant/<int:participant_id>/<int:event_id>/check_valid", methods=["POST"])
def event_check_valid(participant_id, event_id):
	evt = Event.query.filter(
		(Event.participant_id==participant_id) &
		(Event.event_id==event_id) 
		).one()
	if evt:
		if evt.check_valid():
			return redirect("/participant/%s/%s" % (participant_id, event_id))
		else:
			return redirect("/participant/%s" % (participant_id))
	return "error, no event : %s" % event_id
		
@app.route("/participant/<int:participant_id>/<int:event_id>/<int:image_id>/<code>", methods=["POST"])
def event_modify(participant_id, event_id, image_id, code):
	evt = Event.query.filter((Event.participant_id==participant_id) &
							 (Event.event_id==event_id)).one()

	img = Image.query.filter((Image.image_id==image_id) &
							 (Image.participant_id==participant_id)).one()
	if not img: return "no matching image"
	if not evt: return "no matching event"
	if code=="add_image":
		if evt.add_image(img):
			return "success"
		return "add_image failed"
	if code=="split_left":
		if evt.split_left(img):
			return "success"
		return "split_left failed"
	if code=="split_right":
		if evt.split_right(img):
			return "success"
		return "split_right failed"

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
	app.config["SECRET_KEY"] = "secret? what's that?"
	app.run(port=5000, debug=True)
