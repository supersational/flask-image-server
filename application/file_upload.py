from application import app
import os
import time, datetime
import re
import threading
# image processing stuff
import binascii
import PIL
from PIL import Image as PILImage 
from io import BytesIO

# uploads
from config import UPLOAD_FOLDER, APPLICATION_FOLDER, IMAGE_SIZES
from werkzeug import secure_filename
from flask import Response

#csv stuff
import csv

from flask import request, redirect, make_response, jsonify
from application.db import Event, Image, Participant, Study, Label
# for parsing csv into datapoints
from application.db import Datapoint, Datatype
from application.db import session
from application.login import login_required, login_check
from json import dumps as json_dumps
## FILE UPLOAD

ALLOWED_EXTENSIONS = ["csv", "jpg", "jpeg", "png"]
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



# IMAGE_SIZES = {
# 	'thumbnail':{'size':(100, 100),'dir':'thumbnail'},
# 	'medium':{'size':(864, 645),'dir':'medium'},
# 	'full':{'size':(0, 0),'dir':'full'}
# }

# hashed 'pending additions' to the database (so can be confirmed by user)
pending_uploads = {} # should be [time_created, path, participant_id, data to be added to db:=[Image(), Data(), etc.], display_html]
def add_upload(path, participant_id):
	hash = gen_hash() # random hash to allow secure 'landing page' URL
	pending_uploads[hash] = [time.time(), path, participant_id, [], '']
	threading.Timer(0, lambda: process_uploaded_file(hash)).start()
	return hash

axivity_pattern = re.compile(r'B\d{8}_\d\dI\dTA_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})')
thumbnail_size = 256, 256

# extract data that can be added to the db (e.g. Images, .csv -> data)
def process_uploaded_file(hash):
	upload = pending_uploads[hash]
	filename = upload[1]
	filenamebase = os.path.basename(filename).split('.')[0]
	ext = file_extension(filename)
	participant_id = upload[2]
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()
	if ext=='jpg' or ext=='jpeg':
		match = re.match(axivity_pattern, filenamebase)
		#generate a temporary image thumbnail (stored/served in string format)
		im = PILImage.open(os.path.join(UPLOAD_FOLDER, upload[1]))
		with im.copy() as im_thumb:
			stream = BytesIO()
			im_thumb.thumbnail(thumbnail_size)
			im_thumb.save(stream, "JPEG")
			upload[4] = "<img src='data:image//png;base64,%s'\>" % (binascii.b2a_base64(stream.getvalue()), )
			# upload[4] = "<img src='data:image//png;base64,%s'\>" % (binascii.b2a_base64(f.read()), )
		if match:
			g = map(int, match.groups('0'))
			image_time = datetime.datetime(g[0], g[1], g[2], g[3], g[4], g[5])
			upload[3].append('time is: ' + str(image_time))
			
			def gen_path(size):
				return os.path.join('images', str(participant_id),size, filenamebase+".jpg")

			for key, size in IMAGE_SIZES.iteritems():
				outfile = os.path.join(APPLICATION_FOLDER, gen_path(size['dir']))
				ensure_dir_exists(outfile)
				exists = os.path.isfile(outfile)
				if not exists:
					print("    generating : " + key + " " + str(size['size']) + " " + outfile)
					if size['size'][0]>0 and size['size'][1]>0:
						im.thumbnail(size['size'])
					im.save(outfile,"JPEG")

			# if there is already an event we add the image to it
			event_id = getattr(Event.get_event_at_time(image_time, participant_id), 'event_id', None) 
			upload_image = Image(participant_id, image_time, '/'+gen_path('full'), '/'+gen_path('medium'), '/'+gen_path('thumbnail'), event_id=event_id)
			upload[3].append(upload_image)
		else:
			upload[3].append(filenamebase+' not a valid jpg filename')


@app.route("/participant/<int:participant_id>/upload", methods=["GET","POST"])
@login_required
@login_check()
def upload_url(participant_id):
	if request.method=="POST":
		
		confirm_hash = (request.args.get('confirm_hash'))
		if confirm_hash is None:
			# first case is the user will be prompted to view his uploaded files
			return upload_file(participant_id, request.files['file'])
		else:
			# then they can confirm that upload (for a specified pending_upload hash)
			return confirm_upload(confirm_hash)
		
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
					<form action="" method=post><input type=submit></form>
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

def csv_to_data(file):
	columns = []
	column_types = []
	for row in file:
		cols = row.split(",")


def upload_file(participant_id, file):
	print file
	print file.filename
	if file.filename is None or len(file.filename)==0:
		return redirect("/participant/"+str(participant_id)+"/upload?message=invalid filename")
	print file.filename.rsplit('.', 1)[-1]
	print file.filename.rsplit('.', 1)[1]
	ext = file_extension(file.filename) 
	if file and ext in ALLOWED_EXTENSIONS:
		filename = secure_filename(file.filename)
		save_path = os.path.join(UPLOAD_FOLDER, str(participant_id), filename) 
		ensure_dir_exists(save_path)
		file.save(save_path)
		file_hash = add_upload(save_path, participant_id)

		return redirect("/participant/"+str(participant_id)+"/upload?confirm_hash="+file_hash)
	else:
		return redirect("/participant/"+str(participant_id)+"/upload?message=filetype ." + file_extension(file.filename) + " not allowed")


def confirm_upload(hash):
	if hash not in pending_uploads:
		return "hash %s does not exist" % hash

	# confirm what was added by 'process_uploaded_file'
	num_added = 0
	for obj in pending_uploads[hash][3]:
		if isinstance(obj, Image):
			print obj, " is Image"
			session.add(obj)
			num_added += 1
		else:
			print obj, "is type: ", type(obj)
	return "sucessfully added %i objects " % (num_added)