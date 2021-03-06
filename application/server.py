from application import app
from config import  __file__ as application_file

import time # measuring response time
# date handling
import datetime
dateformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")
datetimeformat = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
timeformat = lambda x: datetime.datetime.strptime(x, "%H:%M:%S")
# function wrapping tools
from functools import wraps
from json import dumps as json_dumps
# custom sorting e.g. ['hi10', 'hi1', 'hi2', 'hi3'] -> ['hi1', 'hi2', 'hi3', 'hi10'] 
from application.natsort import natural_sort, natural_keys
# import flask
from flask import Flask, request, redirect, send_from_directory, url_for
from flask import render_template, Response, stream_with_context
from flask.ext.login import login_required, current_user



from application.login import login_check, requires_admin # our login wrappers
# login_manager = LoginManager()
# login_manager.init_app(app)
# import our custom db interface
import application.db as db
# print dir(db)
from application.db import Event, Image, Participant, User, Study, Schema, Label, Folder
db_session = db.session

@app.route("/")
def index():
	return render_template('index.html',
		studies=Study.query.all(),
		participants=Participant.query.all(),
		users=User.query.all(),
		num_images=len(Image.query.all())
		# sql_create=open('application/create_db.txt','r').read(),
		# sql_text=db.read_log()[:2000]
	)
  
@app.route("/reboot_db", methods=["GET"])
# @login_required
# @requires_admin
def reboot_db_page():
	return """<h2>reboot DB options:</h2>
		<form action='/reboot_db' method='POST'> 
			<select name='option'>
					<option value='drop_db'>drop all tables</option>
					<option value='recreate_fake'>Initialize with fake data</option>
					<option value='recreate_real'>Initialize with real data</option>
			</select><br><br>
			<input type="checkbox" name="i_am_sure" value="yes">This will delete all data, are you sure?<br><br>
			<input type='submit' value='Submit'>
		</form>"""
	
@app.route("/reboot_db", methods=["POST"])
# @login_required
# @requires_admin
def reboot_db_action():
	print "reboot_db_action"
	option = request.form['option']
	print option
	if 'i_am_sure' in request.form and request.form['i_am_sure']=="yes":
		if option=='recreate_fake':
			db.drop_db()
			db_session = db.get_session(create_data=True, fake=True)
		elif option=='recreate_real':
			db.drop_db()
			db_session = db.get_session(create_data=True, fake=False)
		elif option=='drop_db':
			db.drop_db()
		return """<p>attempted to %s on the DB</p>""" % (option,), 200
	else:
		return """<p>you must tick the "sure" checkbox (if you are sure)</p>""", 200

def drop_db():
	db.read_log() # clear the log
	db.drop_db()
	drop_sql = db.read_log()
	db_session = db.create_db()
	create_sql = db.read_log()

	# create admin user
	u1 = User('Aiden', 'Aiden', admin=True)
	if len(User.query.filter(User.username==u1.username).all())==0:
	    db_session.add(u1)

	with open('application/create_db.txt','w') as f:
			f.write(create_sql)
	return "<h2>Rebooted DB</h2><h3>Drop SQL:</h3><pre>"+drop_sql+"</pre><h3>Create SQL:</h3><pre>"+create_sql+"</pre>"




@app.route("/images")
@login_required
def images():
	res = "<h1>All Images</h1>\n"
	for image in Image.query.all():
		res += "<img src='%s' href='%s'>" % (image.thumbnail_url, image.full_url)
		# res += " : ".join([str.strip(str(x)) for x in image]) + "<br>\n"
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
		study_users=study.users,
		participants=sorted(study_participants, key=lambda x: natural_keys(x.name)),
		participants_to_add=sorted(participants_to_add, key=lambda x: natural_keys(x.name))
	)

@app.route("/user")
@login_required
def user_self():
	print current_user
	if current_user:
		return user_page(current_user.user_id)


@app.route("/user/<int:user_id>")
@login_required
@login_check()
def user_page(user_id):
	user = User.query.filter(User.user_id==user_id).one()
	user_studies = user.studies
	if current_user.admin is True:
		studies_to_add = [x for x in Study.query.all() if not x in user_studies]
	else:
		studies_to_add = None
	return render_template('user.html', 
		user_id=user_id,
		user_name=user.username,
		studies=sorted(user_studies, key=lambda x: natural_keys(x.name)),
		studies_to_add=studies_to_add,
		can_remove_studies=current_user.admin
	)

@app.route("/user/<int:user_id>/modify_studies", methods=['POST'])
@login_required
@requires_admin
def modify_user_study(user_id):
	study_id, method = request.form['study_id'], request.form['method']
	user = User.query.filter(User.user_id==user_id).one()
	study = Study.query.filter(Study.study_id==study_id).one()
	print user
	print study
	if method=='remove':
		print 'remove'
		if study in user.studies:
			user.studies.remove(study) 
			return redirect('/user/'+str(user_id))
			# return 'success', 200
		else:
			return 'study not in users current studies' + "<br>".join(user.studies), 406
	if method=='add':
		if user is not None and study is not None:
			user.studies.append(study)
			return redirect('/user/'+str(user_id))
	return 'method failed on user_id:' + str(user_id)+ ", study_id: " + str(study_id) + "<br>".join(user.studies), 406

@app.route("/participant/<int:participant_id>")
@login_required
@login_check()
def oneparticipant(participant_id):
	global t0
	t0 = time.time()
	print "participant"
	return render_participant(participant_id)



def stream_template(template_name, **context):
	print "time_before_render_head: ".ljust(40), round(time.time()-t0, 4)

	yield render_template(template_name, only_head=True, **context)
	# print context
	print "time_before_render_tail: ".ljust(40), round(time.time()-t0, 4)

	yield render_template(template_name, skip_head=True, **context)
	print "time_after_render_tail: ".ljust(40), round(time.time()-t0, 4)
	# return "hi"


# @gzipped
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
		if date_max is not None and date_min is not None:
			daterange={'min':date_min,'max':date_max, 'diff':(date_max-date_min).total_seconds()}


	print "time_after_date: ".ljust(40), round(time.time()-t0, 4)

	# according to SQL alchemy this request takes 0.015 seconds:
	# SELECT images.image_id AS images_image_id, images.image_time AS images_image_time, images.participant_id AS images_participant_id, images.event_id AS images_event_id, images.full_url AS images_full_url, images.medium_url AS images_medium_url, images.thumbnail_url AS images_thumbnail_url 
	# FROM images 
	# WHERE %(param_1)s = images.participant_id


	participant = Participant.query.get(participant_id)
	if participant is None:
		return "no participant with that id"
	print "time_after_participant: ".ljust(40), round(time.time()-t0, 4)
	if event is not None:
		images = event.images
		if daterange is not None:
			images = [img for img in images if img.image_time<daterange['max'] and img.image_time > daterange['min']]

	else:
		if daterange is not None:
			print daterange
			images = participant.images.filter((Image.image_time>=daterange['min']) & \
				(Image.image_time<=daterange['max'])).order_by(Image.image_time).limit(600)
		else:
			# this is 0.3s faster.. but takes longer to render template when used
			# images = participant.get_images()
			images = participant.images.order_by(Image.image_time).limit(600)

	print "time_before_get_image_in_range: ".ljust(40), round(time.time()-t0, 4)
		

	print "time_before_sort: ".ljust(40), round(time.time()-t0, 4)
	images = sorted(images, key=lambda x: x.image_time)
	# print "sorted list:"
	# for img in images
	# 	print img, '' if not daterange else str(img.image_time > daterange['max']) + str(img.image_time < daterange['min'])
	print "time_before get by hour: ".ljust(40), round(time.time()-t0, 4)
	images_by_hour = participant.get_images_by_hour()
	print "time_before get SQL text: ".ljust(40), round(time.time()-t0, 4)
	sql_text = ""#db.read_log()[:6000]
	print ("time_before_json_dumps ("+str(len(images))+" images) : ").ljust(40), round(time.time()-t0, 4)
	# render with the first 100 images only
	imgs_array = json_dumps([x.to_array() for x in images[:2000]])
	evts_dict = json_dumps(dict(x.to_array() for x in participant.events))# sorted( evts, key=lambda x: x.start_time)])
	print "time_before_render: ".ljust(40), round(time.time()-t0, 4)
	return Response(stream_with_context(stream_template('participant.html', 
		name=participant.name,
		id=participant.participant_id,
		days=images_by_hour,
		daterange=daterange,
		num_images=participant.num_images,
		schema=json_dumps(participant.schema.to_json()) if participant.schema is not None else Schema("default").to_json(),
		schema_list=Schema.query.all(),
		selected_schema=participant.schema,
		imgs_array=imgs_array,
		# evts_dict=evts_dict,
		**kwargs
	)))

@app.errorhandler(500)
def internal_server_error(error):
	return "Error 500: " + str(error)
@app.errorhandler(400)
def internal_server_error(error):
	return "Error 400: " + str(error)

@app.after_request
def end_timer(response):
	response.calculate_content_length()
	print "size:",(str(response.content_length/1024) + "KB") if response.content_length else "N/A"
	if 't0' in globals():# and str(response._status)!="304 NOT MODIFIED":
		print ("time : "+str(response._status)+"").ljust(40),  str(round(time.time()-t0, 4)).ljust(10), response.mimetype
	return response 

