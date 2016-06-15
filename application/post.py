from application import app

from flask import request, redirect, make_response, jsonify
from application.db import Event, Image, Participant, Study, Label
from application.login import login_required, login_check
from json import dumps as json_dumps
import datetime


@app.route("/user/<int:user_id>/change_password", methods=["POST"])
@login_required
@login_check()
def user_change_password(user_id):
	user = User.query(User.user_id==user_id).one() 
	if user and request.form['old_password']:
		if user.check_password(request.form['old_password']):
			if request.form['new_password']:
				user.set_password(request.form['new_password'])
				return "success", 200
			return "error with new password for user %s" % user_id
		return "error wrong password for user %s" % user_id
	return "error changing user %s password" % user_id


@app.route("/participant/<int:participant_id>/check_valid", methods=["POST"])
@login_required
@login_check()
def event_check_valid(participant_id):
	num_not_valid = 0
	evts = Event.query.filter((Event.participant_id==participant_id)).all()
	for evt in evts:
		if not evt.check_valid():
			num_not_valid += 1
	return "deleted: " + str(num_not_valid) + " invalid events"

@app.route("/participant/<int:participant_id>/<int:event_id>/<int:image_id>/<code>", methods=["POST"])
@login_required
@login_check()
def event_modify(participant_id, event_id, image_id, code):

	evt = Event.query.filter((Event.participant_id==participant_id) &
							 (Event.event_id==event_id)).one()

	img = Image.query.filter((Image.image_id==image_id) &
							 (Image.participant_id==participant_id)).one()
	# print evt
	if 0:
		print "".join(map(lambda x: ('\n'+str(evt.event_id)+' - ') + str(x.image_id) + ": " + str(x.image_time), evt.images))
		if  evt.prev_event is not None:
			# print evt.prev_event
			print "".join(map(lambda x: ('\n'+str(evt.prev_event.event_id)+' - ') + str(x.image_id) + ": " + str(x.image_time), evt.prev_event.images))
		if  evt.next_event is not None:
			# print evt.next_event
			print "".join(map(lambda x: ('\n'+str(evt.next_event.event_id)+' - ') + str(x.image_id) + ": " + str(x.image_time), evt.next_event.images))
	if not img: return jsonify(result="no matching image")  
	if not evt: return jsonify(result="no matching event")
	# create list of images which could have potentially changed
	if code=="add_image":
		changed_images = set(evt.images).union(evt.next_event.images if evt.next_event is not None else []).union(evt.prev_event.images if evt.prev_event is not None else [])
		changed_images |= set(evt.add_image(img)) # merge sets
		return jsonify(images=[x.to_array() for x in changed_images], result='success')
		# return jsonify(result="add_image failed")
	if code=="split_left":
		changed_images = set(evt.images).union(evt.next_event.images if evt.next_event is not None else []).union(evt.prev_event.images if evt.prev_event is not None else [])
		if evt.split_left(img):
			return jsonify(images=[x.to_array() for x in changed_images], result='success')
		return jsonify(result="split_left failed")
	if code=="split_right":
		changed_images = set(evt.images).union(evt.next_event.images if evt.next_event is not None else []).union(evt.prev_event.images if evt.prev_event is not None else [])
		if evt.split_right(img):
			return jsonify(images=[x.to_array() for x in changed_images], result='success')
		return jsonify(result="split_right failed")
	if code=="remove":
		direction = request.form['direction']
		include_target =  request.form['include_target'].lower()=="true"
		print direction, include_target
		cmd = evt.remove_left if direction=="left" else evt.remove_right
		changed_images = cmd(img, include_target=include_target)
		changed_images.append(img)
			 # = set(evt.images).union(evt.next_event.images if evt.next_event is not None else []).union(evt.prev_event.images if evt.prev_event is not None else [])
		return jsonify(images=[x.to_array() for x in changed_images], result='success')
		# return jsonify(result='split '+direction+' failed')


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



@app.route("/participant/<int:participant_id>/<int:image_id>/annotate_image", methods=["POST"])
@login_required
@login_check()
def annotate_image(participant_id, image_id):
	label_id = request.form['label_id']
	label = Label.query.filter(Label.label_id==label_id).one()
	if 'color' in request.form:
		label.color = request.form['color']
	# participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	image = Image.query.filter((Image.participant_id==participant_id) & (Image.image_id==image_id)).one()
	t = image.image_time
	dt = datetime.timedelta.resolution # smallest possible time
	image.event = Event(participant_id, t - dt, t + dt , label_id=label_id)
	changed_images = set([image]) \
		.union(image.event.next_event.images if image.event.next_event is not None else []) \
		.union(image.event.prev_event.images if image.event.prev_event is not None else [])
	print changed_images
	return jsonify(images=[x.to_array() for x in changed_images], result='success')


@app.route("/participant/<int:participant_id>/<int:event_id>/annotate", methods=["POST"])
@login_required
@login_check()
def annotate_event(participant_id, event_id):
	label_id = request.form['label_id']
	label = Label.query.filter(Label.label_id==label_id).one()
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	event = Event.query.filter(Event.event_id==event_id).one()
	event.label = label
	if 'color' in request.form:
		label.color = request.form['color']
	return str(label) + str(participant) + str(event)

@app.route("/participant/<int:participant_id>/load_images", methods=["POST"])
@login_required
@login_check()
def load_images(participant_id):

	start_id = request.form.get('start_id', None) # get with default value
	end_id = request.form.get('end_id', None)
	number = request.form.get('number', None)
	if Participant.query.filter(Participant.participant_id==participant_id).one().has_images is False:
		return jsonify(images=[], query={'start_id':start_id, 'end_id':end_id, 'number':number})

	query = Image.query.filter(Image.participant_id==participant_id).order_by(Image.image_time)

	if start_id != None:
		start_id = int(start_id)
		start_img = Image.query.filter(Image.image_id==start_id).one()
		query = query.filter(Image.image_time>start_img.image_time)


	if end_id is not None:
		end_id = int(end_id)
		end_img = Image.query.filter(Image.image_id==end_id).one()
		query = query.filter(Image.image_time<end_img.image_time)


	if number is not None:
		images = query.limit(number)
	else:
		images = query.all()
	# images = sorted(images, key=lambda x: x.image_time)


	print "to array() :"
	print "\n".join([str([x.image_id, x.is_first, x.is_last, x.image_time]) for x in images])
	print [x.to_array()[5] for x in images]
	for e in set([img.event for img in images]):
		if e is None:
			continue
		print e.event_id
		print e.first_image.image_id, e.first_image.image_time
		print e.last_image.image_id, e.last_image.image_time
	return jsonify(images=[x.to_array() for x in images], query={'start_id':start_id, 'end_id':end_id, 'number':number})#)", 200, {'Content-type', 'application/json'})



# download csv of the annotations
# note: not technically a post request, but still belongs here for now..
@app.route("/participant/<int:participant_id>/download_annotation", methods=["GET"])
@login_required
@login_check()
def generate_annotation(participant_id):
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	participant_name = participant.name
	images = participant.images
	events = participant.events

	output = BytesIO()
	writer = csv.writer(output)
	writer.writerow(["name","image_time","annotation"])
	for img in sorted(images, key=lambda x: x.image_time):
		annotation = ""
		if img.event:
			if img.event.label:
				annotation = img.event.label.name
		writer.writerow([participant_name,img.image_time,annotation])

	response = make_response(output.getvalue())
	response.headers["Content-Disposition"] = "attachment; filename=annotation.csv"
	return response
