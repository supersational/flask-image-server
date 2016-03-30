from imant import app
from flask import request, redirect
from imant.db import Event, Image, Participant, Study, Label
from imant.login import login_required, login_check
from json import dumps as json_dumps


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
	# print evt
	print "".join(map(lambda x: ('\n'+str(evt.event_id)+' - ') + str(x.image_id) + ": " + str(x.image_time), evt.images))
	if  evt.prev_event is not None:
		# print evt.prev_event
		print "".join(map(lambda x: ('\n'+str(evt.prev_event.event_id)+' - ') + str(x.image_id) + ": " + str(x.image_time), evt.prev_event.images))
	if  evt.next_event is not None:
		# print evt.next_event
		print "".join(map(lambda x: ('\n'+str(evt.next_event.event_id)+' - ') + str(x.image_id) + ": " + str(x.image_time), evt.next_event.images))
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
	event = Event.query.filter(Event.event_id==event_id).one()
	event.label = label
	return str(label) + str(participant) + str(event)
	if study and participant:
		if study in participant.studies:
			participant.studies.remove(study)	
			return redirect("/study/" + study_id)
		else:
			return "participant not in that study"
	return "Method = " + request.method + " study_id : " + str(study_id) + " participant_id : " + str(participant_id)

@app.route("/participant/<int:participant_id>/load_images", methods=["POST"])
@login_required
@login_check()
def load_images(participant_id):
	query = Image.query.filter(Image.participant_id==participant_id)
	try:
		start_id = int(request.form['start_id'])
		query.filter(Image.image_id>=start_id)
	except ValueError:
		start_id = float("inf")
	try:
		end_id = int(request.form['end_id'])
	except ValueError:
		end_id = -float("inf")
	try:
		number = int(request.form['number'])
	except ValueError:
		number = None

	if number is not None:
		images = query.limit(number)
	else:
		images = query.all()
	# 	images = Image.query.filter((Image.participant_id==participant_id) & (Image.image_id>=start_id) & (Image.image_id<=end_id)).limit(number)
	# else:
	# 	images = Image.query.filter((Image.participant_id==participant_id) & (Image.image_id>=start_id) & (Image.image_id<=end_id))
	return json_dumps([x.to_array() for x in images])