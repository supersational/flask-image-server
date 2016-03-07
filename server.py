# date handling
import datetime
dateformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")
datetimeformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
timeformat = lambda x: datetime.datetime.strptime(x, "%H:%M:%S")
# function wrapping tools
from functools import wraps
# custom sorting e.g. ['hi10', 'hi1', 'hi2', 'hi3'] -> ['hi1', 'hi2', 'hi3', 'hi10'] 
from natsort import natural_sort, natural_keys
# import flask
from flask import Flask, request, redirect, send_from_directory, url_for
from flask import render_template, Response, stream_with_context
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

# automatically checks for user access to study_id, participant_id, or user_id (all specified by <int:study_id> etc. in kwargs)
def login_check():
	def true_decorator(f):
		@wraps(f)
		def wrapped(*args, **kwargs):
			# print "wrapped"
			# print args, kwargs
			# print current_user
			if not current_user:
				return render_template('login.html', message="You must be logged in to view this page")
			if current_user.admin is True:
				return f(*args, **kwargs)

			if 'study_id' in kwargs:
				print 'study_id ', kwargs['study_id']
				if not Study.query.filter(Study.study_id==kwargs['study_id']).one() in current_user.studies:
					return render_template('login.html', message="You do not have access to this study")
			if 'participant_id' in kwargs:
				print 'participant_id ', kwargs['participant_id']
				if not Participant.query.filter(Participant.participant_id==kwargs['participant_id']).one() in \
					[study.participants for study in current_user.studies]:
					return render_template('login.html', message="You do not have access to this participant")
			if 'user_id' in kwargs:
				print 'user_id ', kwargs['user_id']
				if not User.query.filter(User.user_id==kwargs['user_id']).one()==current_user:
					return render_template('login.html', message="You do not have access to this user")
			return f(*args, **kwargs)
		return wrapped
	return true_decorator


login_manager.login_view = 'login'
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')

	username = request.form['username']
	password = request.form['password']
	print username, password
	registered_user = User.query.filter_by(username=username).first()
	print registered_user
	print request.endpoint
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
    return send_from_directory('images', filename, cache_timeout=60*60)

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
@login_required
@login_check()
def user(user_id):
	user = User.query.filter(User.user_id==user_id).one()
	res = "<h2> User: " + user.username + " (" + str(user_id) + ")</h2>\n"
	res += "<h4> User has access to the following studies: </h4>\n"
	for study in user.studies:
		res += "Study: %s, id: %s, has %s participants %s <br>\n" % (study.name, study.study_id, len(study.participants), dir(study))
	return res

@app.route("/study/<int:study_id>")
@login_required
@login_check()
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
@login_required
@login_check()
def oneparticipant(participant_id):
	global t0
	t0 = time.time()
	return render_participant(participant_id)


@app.route("/participant/<int:participant_id>/<int:event_id>")
@login_required
@login_check()
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


def stream_template(template_name, **context):
	yield render_template(template_name, only_head=True, **context)
	# print context
	yield render_template(template_name, skip_head=True, **context)
	# return "hi"


def render_participant(participant_id, event=None, kwargs={}):
	daterange = None

	print "time_before_date: ".ljust(40), round(time.time()-t0, 4)

	if "date_min" in request.args.keys() and "date_max" in request.args.keys():
		date_min = request.args.get('date_min', default=None, type=datetimeformat)
		date_max = request.args.get('date_max', default=None, type=datetimeformat)
		if date_max is None:
			# fails parsing 24:00:00 so add special case
			if request.args['date_max'].split('T')[1][0:2]=='24':
				date_max = datetimeformat(request.args['date_max'].replace('T24:', 'T23:'))
				date_max += datetime.timedelta(hours=1)
		daterange={'min':date_min,'max':date_max}


	print "time_after_date: ".ljust(40), round(time.time()-t0, 4)

	# according to SQL alchemy this request takes 0.015 seconds:
	# SELECT images.image_id AS images_image_id, images.image_time AS images_image_time, images.participant_id AS images_participant_id, images.event_id AS images_event_id, images.full_url AS images_full_url, images.medium_url AS images_medium_url, images.thumbnail_url AS images_thumbnail_url 
	# FROM images 
	# WHERE %(param_1)s = images.participant_id


	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	print "time_after_participant: ".ljust(40), round(time.time()-t0, 4)
	if event is not None:
		images = event.images
		if daterange is not None:
			images = [img for img in images if img.image_time<daterange['max'] and img.image_time > daterange['min']]

	else:
		if daterange is not None:
			print daterange
			images = participant.images.filter((Image.image_time>=daterange['min']) & \
				(Image.image_time<=daterange['max'])).order_by(Image.image_time).limit(100)
		else:
			# this is 0.3s faster.. but takes longer to render template when used
			# images = participant.get_images()
			images = participant.images.order_by(Image.image_time).limit(100)

	print "time_before_get_image_in_range: ".ljust(40), round(time.time()-t0, 4)
		

	print "time_before_sort: ".ljust(40), round(time.time()-t0, 4)
	images = sorted(images, key=lambda x: x.image_time)
	# print "sorted list:"
	# for img in images
	# 	print img, '' if not daterange else str(img.image_time > daterange['max']) + str(img.image_time < daterange['min'])
	print "time_before get by hour: ".ljust(40), round(time.time()-t0, 4)
	images_by_hour = participant.get_images_by_hour()
	print "time_before get SQL text: ".ljust(40), round(time.time()-t0, 4)
	sql_text = db.read_log()[:6000]

	print "time_before_render: ".ljust(40), round(time.time()-t0, 4)
	return Response(stream_with_context(stream_template('participant.html', 
		name=participant.name,
		id=participant.participant_id,
		images=images[:100], # TODO :  flask.ext.sqlalchemy.Pagination
		days=images_by_hour,
		daterange=daterange,
		num_images=len(images),
		sql_text=sql_text,
		schema=Schema.query.first(),
		schema_list=Schema.query.filter(),
		**kwargs
	)))


@app.route("/participant/<int:participant_id>/<int:event_id>/check_valid", methods=["POST"])
@login_required
@login_check()
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
@login_required
@login_check()
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
	if code=="remove":
		direction = request.form['direction']
		include_target =  request.form['include_target'].lower()=="true"
		print direction, include_target
		cmd = evt.remove_left if direction=="left" else evt.remove_right
		if cmd(img, include_target=include_target):
			return "success"
		return "remove_"+direction+" failed"
	# if code=="remove_right":
	# 	if evt.remove_right(img):
	# 		return "success"
	# 	return "remove_right failed"

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
@login_required
@login_check()
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
	if 't0' in globals() and str(response._status)!="304 NOT MODIFIED":
		print ("time : "+str(response._status)+"").ljust(40),  str(round(time.time()-t0, 4)).ljust(10), response.mimetype
	return response

if __name__ == "__main__":
	print "running on port 5000"
	app.config["SECRET_KEY"] = "secret? what's that?"
	app.run(port=5000, debug=True)
	# app = ProfilerMiddleware(app)
