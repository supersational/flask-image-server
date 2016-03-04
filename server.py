# date handling
import datetime
dateformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")
datetimeformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
timeformat = lambda x: datetime.datetime.strptime(x, "%H:%M:%S")
# custom sorting e.g. ['hi10', 'hi1', 'hi2', 'hi3'] -> ['hi1', 'hi2', 'hi3', 'hi10'] 
from natsort import natural_sort, natural_keys
# import flask
from flask import Flask, request, redirect, send_from_directory, url_for
from flask import render_template
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
# profiling
from werkzeug.contrib.profiler import ProfilerMiddleware

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
	elif not registered_user.check_password(password):
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
		sql_text=db.read_log()[:2000]
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
		participants=sorted(study_participants, key=lambda x: natural_keys(x.name)),
		participants_to_add=sorted(participants_to_add, key=lambda x: natural_keys(x.name)),
		sql_text=db.read_log()[:2000]
	)


@app.route("/participant/<int:participant_id>")
def oneparticipant(participant_id):
	global t0
	t0 = time.time()
	return render_participant(participant_id)


@app.route("/participant/<int:participant_id>/<int:event_id>")
def render_event(participant_id, event_id):
	global t0
	t0 = time.time()
	event = Event.query.filter(Event.event_id==event_id, Event.participant_id==participant_id).one()
	kwargs = {}
	kwargs['prev_event_id']=getattr(event.prev_event, 'event_id', None) # None as default if no prev_event exists
	kwargs['next_event_id']=getattr(event.next_event, 'event_id', None)
	kwargs['prev_image']=event.prev_image
	kwargs['next_image']=event.next_image
	kwargs['event_id']=event.event_id
	kwargs['event_seconds']=event.length.total_seconds()
	return render_participant(participant_id, event=event, kwargs=kwargs)

	
def render_participant(participant_id, event=None, kwargs={}):
	daterange = None
	t1 = time.time()
	print "time_before_date: ", t1-t0

	if "date_min" in request.args.keys() and "date_max" in request.args.keys():
		date_min = request.args.get('date_min', default=None, type=datetimeformat)
		date_max = request.args.get('date_max', default=None, type=datetimeformat)
		if date_max is None:
			# fails parsing 24:00:00 so add special case
			if request.args['date_max'].split('T')[1][0:2]=='24':
				date_max = datetimeformat(request.args['date_max'].replace('T24:', 'T23:'))
				date_max += datetime.timedelta(hours=1)
		daterange={'min':date_min,'max':date_max}

	t1 = time.time()
	print "time_after_date: ", t1-t0

	# according to SQL alchemy this request takes 0.015 seconds:
	# SELECT images.image_id AS images_image_id, images.image_time AS images_image_time, images.participant_id AS images_participant_id, images.event_id AS images_event_id, images.full_url AS images_full_url, images.medium_url AS images_medium_url, images.thumbnail_url AS images_thumbnail_url 
	# FROM images 
	# WHERE %(param_1)s = images.participant_id

	t1 = time.time()
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	print "time_after_participant: ", t1-t0
	if event is not None:
		images = event.images
	else:
		images = participant.images

	t1 = time.time()
	print "time_before_get_image_in_range: ", t1-t0
		
	if daterange is not None:
		images = [img for img in images if img.image_time<daterange['max'] and img.image_time > daterange['min']]
	t1 = time.time()
	print "time_before_sort: ", t1-t0
	images = sorted(images, key=lambda x: x.image_time)
	# print "sorted list:"
	# for img in images
	# 	print img, '' if not daterange else str(img.image_time > daterange['max']) + str(img.image_time < daterange['min'])
	t1 = time.time()
	print "time_before_render: ", t1-t0
	return render_template('participant.html', 
		name=participant.name,
		id=participant.participant_id,
		images=images[:100],
		days=participant.get_images_by_hour(),
		daterange=daterange,
		num_images=len(images),
		sql_text=db.read_log()[:6000],
		schema=Schema.query.first(),
		schema_list=Schema.query.filter(),
		**kwargs
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

@app.route("/participant/<int:participant_id>/<int:event_id>/annotate", methods=["POST"])
def annotate(participant_id, event_id):
	label_id = request.form['label_id']
	label = Label.query.filter(Label.label_id==label_id).one()
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	event = event.query.filter(event.event_id==event_id).one()
	return str(label) + str(participant) + str(event)
	if study and participant:
		if study in participant.studies:
			participant.studies.remove(study)	
			return redirect("/study/" + study_id)
		else:
			return "participant not in that study"
	return "Method = " + request.method + " study_id : " + str(study_id) + " participant_id : " + str(participant_id)

@app.errorhandler(500)
def internal_server_error(error):
	return "Error 500: " + str(error)

import time
@app.before_request
def start_timer():
	pass

@app.after_request
def end_timer(response):
	t1 = time.time()
	print "time : ", t1-t0
	return response

if __name__ == "__main__":
	print "running on port 5000"
	app.config["SECRET_KEY"] = "secret? what's that?"
	app.run(port=5000, debug=True)
	# app = ProfilerMiddleware(app)
