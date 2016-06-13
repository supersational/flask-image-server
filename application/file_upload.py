from application import app
import os
import time
# uploads
from config import UPLOAD_FOLDER
from werkzeug import secure_filename
from flask import Response

#csv stuff
import csv
from io import BytesIO

from flask import request, redirect, make_response, jsonify
from application.db import Event, Image, Participant, Study, Label
from application.login import login_required, login_check
from json import dumps as json_dumps
## FILE UPLOAD

ALLOWED_EXTENSIONS = ["csv", "js","jpg","png"]
def file_extension(filename):
	return '' if '.' not in filename else filename.rsplit('.', 1)[1]

def ensure_dir_exists(directory):
	if not os.path.exists(os.path.dirname(directory)):
		os.makedirs(os.path.dirname(directory))

# hashed 'pending additions' to the database (so can be confirmed by user)
pending_uploads = {} # should be [time_created, participant_id, data to be added to db:=[Image(), Data(), etc.]]
# this function generates a random hash
import random
def gen_hash():
	hash = random.getrandbits(128)
	return "%032x" % hash

@app.route("/participant/<int:participant_id>/upload", methods=["GET","POST"])
@login_required
@login_check()
def upload_file(participant_id):
	if request.method=="POST":
		file = request.files['file']
		print file
		print file.filename
		if file.filename is None or len(file.filename)==0:
			return redirect("/participant/"+str(participant_id)+"/upload?message=invalid filename")
		print file.filename.rsplit('.', 1)[-1]
		print file.filename.rsplit('.', 1)[1]
		ext = file_extension(file.filename) 
		if file and ext in ALLOWED_EXTENSIONS:
			if ext!='csv':
				filename = secure_filename(file.filename)
				save_path = os.path.join(UPLOAD_FOLDER, str(participant_id), filename)
				ensure_dir_exists(save_path)
				file.save(save_path)
				return redirect("/participant/"+str(participant_id)+"/upload?message=request successful")
			else:
				hash = gen_hash()
				data_array = []
				pending_uploads[hash] = [time.time(), participant_id, data_array]
				def generate():
					yield '''
					    <!doctype html>
					    <title>''' + file.filename + '''</title><h1>csv detected:</h1>
					    <button onclick="location.href='%s'">Press here to add the following data:</button><br><br>''' % ("/participant/"+str(participant_id)+"/upload?confirm_hash="+hash)
					for row in file:
						data_array.append(row)
						yield row + '<br>'
				return Response(generate())
		else:
			return redirect("/participant/"+str(participant_id)+"/upload?message=filetype ." + file_extension(file.filename) + " not allowed")
	else:
		message = ('<p>'+request.args.get('message')+'</p>') if request.args.get('message') is not None else ''
		confirm_hash = (request.args.get('confirm_hash')) if request.args.get('confirm_hash') is not None else ''
		print "message: ", message
		print "confirm_hash: ", confirm_hash
		if len(confirm_hash)>0:
			if confirm_hash not in pending_uploads:
				return '''
			    <!doctype html>
			    <title>Not confirmed</title>
			    <h1>hash: %s not valid</h1>''' % (confirm_hash,)
			
			upload = pending_uploads[confirm_hash]
			return '''
			    <!doctype html>
			    <title>Confirmed</title>
			    <h1>Confirmed addtion to db:</h1>
			    <p>%s</p> 
			    <p>participant_id: %s</p>
			    %s
	    		''' % (upload[0],upload[1], "<br>".join(upload[2]))
		else:
			return '''
			    <!doctype html>
			    <title>Upload new File</title>
			    <p>%s</p>
			    <h1>Upload new participant file</h1>
			    <form action="" method=post enctype=multipart/form-data>
			      <p><input type=file name=file>
			         <input type=submit value=Upload>
			    </form>
	    		''' % (message,)

# Logic for parsing file to datapoints
from application.db import Datapoint, Datatype, Participant

def csv_to_data(file):
	columns = []
	column_types = []
	for row in file:
		cols = row.split(",")