from application import app
import os
import time, datetime
import re
import threading
# image processing stuff
import binascii
import PIL
import cgi
from PIL import Image as PILImage 
from io import BytesIO

# uploads
from config import UPLOAD_FOLDER, APPLICATION_FOLDER, IMAGE_SIZES
from config import SUPPORTED_IMAGE_EXTENSIONS, SUPPORTED_DATA_EXTENSIONS
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
from application import image_processing
from json import dumps as json_dumps
## FILE UPLOAD

ALLOWED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS + SUPPORTED_DATA_EXTENSIONS  # == ["csv", "jpg", "jpeg", "png"]
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


axivity_pattern = re.compile(r'B\d{8}_\d\dI\dTA_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})')
thumbnail_size = 256, 256

# extract data that can be added to the db (e.g. Images, .csv -> data)
# and save the image as thumbnail, medium etc.
def process_file_thread(hash, filename):
	print "processing :", filename
	upload = pending_uploads[hash]
	upload_file = upload['files'][filename]
	filenamebase = os.path.basename(filename).split('.')[0]
	ext = file_extension(filename)
	participant_id = upload['participant_id']
	participant = Participant.query.filter(Participant.participant_id==participant_id).one()


	if ext in SUPPORTED_IMAGE_EXTENSIONS:
		
		upload_file['display'] += image_processing.to_html_img(filename, size=IMAGE_SIZES['thumbnail']['size'])
		print filename, participant_id
		image = Image.from_file(filename, participant_id)
		if image is not None:
			upload_file['display'] += '<p>Image date extracted: %s</p>' % (str(image.image_time), )
			upload_file['data'].append(image)
		else:
			upload_file['display'] += '<p> %s is not a valid jpg filename</p>' % (filenamebase,)

	if ext=='csv':
		datafile = Datafile(filenamebase)
		upload_file['data'].append(datafile)
		with open(filename, 'rb') as csvfile:
			csvreader = csv.reader(csvfile)
			firstrow = next(csvreader)
			datatypes = map(Datatype.get_or_create, firstrow)
			time_cols = []
			for column_name in firstrow:
				acc_parser = parse_acc_header(column_name)
				if acc_parser:
					time_cols.append(i)
					datatypes[i] = None

			# for i, col in enumerate(firstrow):
			# 	print i, col
			# 	datatype = Datatype.get_or_create(col)
			# 	datatypes[i] = datatype
			print datatypes
			# upload_file['data'].extend(datatypes)
			limit = 100

			for row in csvreader:
				print ', '.join(row)
				for i, col in enumerate(row):
					if i in time_cols:
						pass
						# parse datetime
					print i, col
					try:
						val = float(col)
					except ValueError:
						print "not a float"
						val = 0
					datapoint = Datapoint(datetime.datetime.now(), val, upload['participant_id'])
					datatypes[i].datapoints.append(datapoint)
					datafile.datapoints.append(datapoint)
				limit -= 1
				if limit < 0: 
					break

acc_header = re.compile(r'acceleration \(mg\) - (\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d) - \d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d - sampleRate = (\d)+ seconds')
def parse_acc_header(col):
	match = re.match(acc_header, col)
	if match:
		g = match.groups
		return (datetime.datetime(g(0),g(1),g(2), g(3),g(4),g(5)), datetime.timedelta(seconds=g(6)))
	else: return None
@app.route("/participant/<int:participant_id>/upload", methods=["GET","POST"])
@login_required
@login_check()
def upload_url(participant_id):
	if request.method=="POST":
		
		confirm_hash = (request.args.get('confirm_hash'))
		if confirm_hash is None:
			# first case is the user will be prompted to view his uploaded files

			return save_file(participant_id, request.files.getlist('file'))
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
				html += '''<h1>hash: %s not in pending_uploads</h1><p>%s</p>''' % (confirm_hash,cgi.escape(str(pending_uploads)))
			else:
				upload = pending_uploads[confirm_hash]
				html += '''
					<h1>Upload successful:</h1>
					<form action="" method=post><input type=submit value="Add this data pernamently"></form>
					<p>%s</p> 
					<p>participant_id: %s</p>
					<h3>extracted data:</h3>
					<p>%s</p>
					%s<br>''' % (
						datetime.datetime.fromtimestamp(upload['time']).strftime('%Y-%m-%d %H:%M:%S'),
						upload['participant_id'],
						"</p><p>".join(map(lambda x: str(upload['files'][x]['data']),upload['files'])), 
						"".join([upload['files'][x]['display'] for x in upload['files']]) 
						)

			html += '''<a href='/participant/%i/upload'><button>Upload new file<button?</a> ''' % (participant_id, )
		else:
			html += '''
				<p>%s</p>
				<h1>Upload new participant file</h1>
				<form action="" method=post enctype=multipart/form-data>
				<p><input type=file name=file multiple>
				<input type=submit value=Upload>
				</form>
				''' % (message,)
		return html

def csv_to_data(file):
	columns = []
	column_types = []
	for row in file:
		cols = row.split(",")

# when a file is submitted
def save_file(participant_id, files):
	hash = gen_hash() # random hash to allow secure 'landing page' URL
	pending_uploads[hash] = {
		'time':time.time(),
		'participant_id':participant_id,
		'files':{}
	}

	for file in files:

		# [time.time(), participant_id, [], '']
		
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

			
			pending_uploads[hash]['files'][save_path] = {
				'ext':ext,
				'data':[],
				'display':'<p>upload: ' + save_path + "</p>"
				}

			process_file_thread(hash, save_path)
			# threading.Timer(0, lambda: process_file_thread(hash, save_path)).start()

	return redirect("/participant/"+str(participant_id)+"/upload?confirm_hash="+hash)
	# else:
	# 	return redirect("/participant/"+str(participant_id)+"/upload?message=filetype ." + file_extension(file.filename) + " not allowed")


# confirm what was added by 'process_file_thread'
def confirm_upload(hash):
	if hash not in pending_uploads:
		return "hash %s does not exist" % hash

	num_images = 0
	num_datapoints = 0
	added_html = ''
	for file in pending_uploads[hash]['files'].itervalues():
		for obj in file['data']:
			if isinstance(obj, Image):
				print obj, " is Image"
				session.add(obj)
				session.flush()
				num_images += 1
			elif isinstance(obj, Datatype) or isinstance(obj, Datapoint):
				added_html += "<p>%s</p>" % (str(obj),)
				session.add(obj)
				session.flush()
				num_datapoints += 1
				added_html += "<p>%s</p>" % (str(obj),)
			elif isinstance(obj, Datafile):
				session.add(obj)
				session.flush()
				num_datapoints += len(obj.datapoints)
				added_html += "<p>%s</p>" % (str(obj),)
			else:
				print obj, "is type: ", type(obj)
	return "sucessfully added %i images and %i dataponts: %s " % (num_images, num_datapoints, added_html)
