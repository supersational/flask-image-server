from application import app
import os
import time, datetime
import re
import threading
import binascii
import PIL
from PIL import Image as PILImage
from io import BytesIO

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
	return '' if '.' not in filename else filename.rsplit('.', 1)[1].lower()

def ensure_dir_exists(directory):
	if not os.path.exists(os.path.dirname(directory)):
		os.makedirs(os.path.dirname(directory))



# this function generates a random hash
import random
def gen_hash():
	hash = random.getrandbits(128)
	return "%032x" % hash




# hashed 'pending additions' to the database (so can be confirmed by user)
pending_uploads = {} # should be [time_created, path, participant_id, data to be added to db:=[Image(), Data(), etc.], display_html]
def add_upload(path, participant_id):
	hash = gen_hash() # random hash to avoid collisions
	pending_uploads[hash] = [time.time(), path, participant_id, [], '']
	threading.Timer(0, lambda: process_uploaded_file(hash)).start()
	return hash

axivity_pattern = re.compile(r'B\d{8}_\d\dI\dTA_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})')
thumbnail_size = 256, 256
def process_uploaded_file(hash):
	upload = pending_uploads[hash]
	filename = upload[1]
	filenamebase = os.path.basename(filename).split('.')[0]
	ext = file_extension(filename)
	if ext=='jpg' or ext=='jpeg':
		match = re.match(axivity_pattern, filenamebase)
		with PILImage.open(os.path.join(UPLOAD_FOLDER, upload[1])) as im:
			stream = BytesIO()
			im.thumbnail(thumbnail_size)
			im.save(stream, "JPEG")
			upload[4] = "<img src='data:image//png;base64,%s'\>" % (binascii.b2a_base64(stream.getvalue()), )
			# upload[4] = "<img src='data:image//png;base64,%s'\>" % (binascii.b2a_base64(f.read()), )
		if match:
			g = map(int, match.groups('0'))
			image_time = datetime.datetime(g[0], g[1], g[2], g[3], g[4], g[5])
			upload[3].append('time is: ' + str(image_time))
		else:
			upload[3].append(filenamebase+' not a valid jpg filename')


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
			filename = secure_filename(file.filename)
			save_path = os.path.join(str(participant_id), filename) 
			full_save_path = os.path.join(UPLOAD_FOLDER, save_path)
			ensure_dir_exists(full_save_path)
			file.save(full_save_path)
			file_hash = add_upload(save_path, participant_id)
			# if ext!='csv':
			return redirect("/participant/"+str(participant_id)+"/upload?confirm_hash="+file_hash)
			# else:
				
			# 	def generate():
			# 		yield '''
			# 		    <!doctype html>
			# 		    <title>''' + file.filename + '''</title><h1>csv detected:</h1>
			# 		    <button onclick="location.href='%s'">Press here to add the following data:</button><br><br>''' % ("/participant/"+str(participant_id)+"/upload?confirm_hash="+hash)
			# 		for row in file:
			# 			data_array.append(row)
			# 			yield row + '<br>'
			# 	return Response(generate())
		else:
			return redirect("/participant/"+str(participant_id)+"/upload?message=filetype ." + file_extension(file.filename) + " not allowed")
	else:
		message = ('<p>'+request.args.get('message')+'</p>') if request.args.get('message') is not None else ''
		confirm_hash = (request.args.get('confirm_hash')) if request.args.get('confirm_hash') is not None else ''
		print "message: ", message
		print "confirm_hash: ", confirm_hash
		html =  '''<!doctype html><title>Upload complete</title>'''
		if len(confirm_hash)>0:
			if confirm_hash not in pending_uploads:
				html += '''<h1>hash: %s not in pending_uploads</h1>''' % (confirm_hash,)
			else:
				upload = pending_uploads[confirm_hash]
				html += '''
					<h1>Confirmed addition to db:</h1>
					<p>%s</p> 
					<p>path: %s</p>
					<p>participant_id: %s</p>
					<h3>extracted data:</h3>
					<p>%s</p>
					%s<br>''' % (
						datetime.datetime.fromtimestamp(upload[0]).strftime('%Y-%m-%d %H:%M:%S'),
						upload[1],
						upload[2],
						"</p><p>".join(map(str,upload[3])), 
						upload[4]
						)

			html += '''<a href='/participant/%i/upload'><button>Upload new file<button?</a> ''' % (participant_id, )
		else:
			html += '''
				<p>%s</p>
				<h1>Upload new participant file</h1>
				<form action="" method=post enctype=multipart/form-data>
				<p><input type=file name=file>
				<input type=submit value=Upload>
				</form>
				''' % (message,)
		return html
# Logic for parsing file to datapoints
from application.db import Datapoint, Datatype, Participant

def csv_to_data(file):
	columns = []
	column_types = []
	for row in file:
		cols = row.split(",")