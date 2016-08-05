from application import app
import os
import time, datetime
from dateutil.parser import parse
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
from flask import render_template
#csv stuff
import csv

from flask import request, redirect, make_response, jsonify
from sqlalchemy.exc import InvalidRequestError
from application.db import Event, Image, Participant, Study, Label
# for parsing csv into datapoints
from application.db import Datapoint, Datatype
from application.db import session
from application.login import login_required, login_check
from application import image_processing
from application import bokeh_plot
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
		csv_datapoints, csv_html = processCSV(filename)
		upload_file['display'] += csv_html
		upload_file['datapoints'].extend(csv_datapoints)

def processCSV(filename):
	# datafile = Datafile(filenamebase)
	# upload_file['data'].append(datafile)
	parsing_start_time = time.time()
	csv_html = ""
	csv_datapoints = []
	with open(filename, 'rb') as csvfile:
		try:
			dialect = csv.Sniffer().sniff(csvfile.read(1024))
		except csv.Error:
			dialect = csv.excel
		csvfile.seek(0)

		csvreader = csv.reader(csvfile, dialect)
		column_headers = next(csvreader)
		time_cols = []
		get_time = None
		datatypes = [None for n in column_headers] 
		# check for "acceleration (mg) - 2016-01-28 17:58:00 - 2016-01-28 18:48:00 - sampleRate = 5 seconds"
		if any(map(find_special_header, column_headers)):
			# file is AccTimeSeries.csv
			for i, column_name in enumerate(column_headers):
				acc_parser = find_special_header(column_name)
				if acc_parser:
					# time_cols.append(i)
					start_time = acc_parser[0]
					timedelta = acc_parser[1]
					get_time = lambda rownum, row: start_time + timedelta * rownum  
					datatypes[i] = Datatype.get_or_create('acceleration')
				else:
					datatypes[i] = Datatype.get_or_create(column_name)
		else:
			# for a csv with a time column, we take the first one that successfully parses as a date
			# get_time must be a valid function for extracting a date from a row
			first_row = next(csvreader)
			for i, col in enumerate(first_row):
				try: 
					print "time string found at col", i, col
					parse(col, fuzzy=False)
					csv_html += "<p>"+filename+" </p><p>time col[" + str(i) + "] = " + col +"</p>"
					time_cols.append(i) 
					get_time = lambda rownum, row, colnum=i: parse(row[colnum], fuzzy=False) if 0<=colnum<len(row) else None
					break
				except ValueError:
					pass
			datatypes = map(Datatype.get_or_create, column_headers)
			
			# reset csvreader to read first row
			csvreader = csv.reader(csvfile)
			next(csvreader)

		csv_html += "<p>"+filename+" dialect= " + str(dialect) + "</p>"
		for p in ['escapechar', 'lineterminator', 'quotechar', 'quoting', 'skipinitialspace']:
			csv_html += "<p>"+p+ ":"+str(getattr(dialect, p)) +"</p>"


		if get_time is None:
			print "can't get time"
			print dir(locals())
			csv_html += "<p>"+filename+" didn't have any time columns in</p><ul>"
			first_row = next(csvreader)
			for i, col in enumerate(first_row):
				csv_html += "<li>"+str(i)+": " + col +" </li>"
			csv_html += "</ul>"

		else:
			print csv_html.replace("</p>","</p>\n")
			limit = 1000000
			datatypes_id = map(lambda x: x.datatype_id if x else None, datatypes)
			errorTypes = {
				'no_time_col':0,
				'no_float_convert':0,
				'no_datatype_exist':0,
				'limit_reached':False,
			}
			for rownum, row in enumerate(csvreader):
				# print rownum, row
				t = get_time(rownum, row)
				if t is None:
					errorTypes['no_time_col'] += 1
					print "time row did not exist at row %i: %s \n %s" % (rownum, str(row), str(0 in row))
					break
				
				# print row, t
				# print ', '.join(row)
				for colnum, col in enumerate(row):
					if colnum in time_cols:
						# print col, "in time_cols"
						continue
						# parse datetime
					# print colnum, col
					try:
						val = float(col)
					except ValueError:
						print colnum, col, "not a float"
						errorTypes['no_float_convert'] += 1
						val = 0

					datatype_id = datatypes_id[colnum]
					if datatype_id:
						csv_datapoints.append([t, val, datatype_id])
					else:
						errorTypes['no_datatype_exist'] += 1
						print val, colnum,  "no datatype_id"
				limit -= 1
				if limit < 0: 
					errorTypes['limit_reached'] = True
					break
			print datatypes
			print time_cols
			print("--- .csv parsing %s rows took %s seconds ---" % (rownum, time.time() - parsing_start_time))
			print("--- %s datapoints were added ---" % len(csv_datapoints))
			csv_html += "".join(["<p>"+key+":"+str(value)+"</p>" for key, value in errorTypes.iteritems()])

	for i, d in enumerate(datatypes):
		print str(i) + ":" + str(d)
		csv_html += "<p>"+str(i) + ":" + str(d) +"</p>"
	return csv_datapoints, csv_html

acc_header = re.compile(r'acceleration \(mg\) - (\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d) - \d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d - sampleRate = (\d)+ seconds')
def find_special_header(col):
	match = re.match(acc_header, col)
	if match:
		g = map(int, match.groups())
		# print map(int,g(0))
		print g
		return (datetime.datetime( *tuple(g[0:5])), datetime.timedelta(seconds=g[6]))
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
				added_data = []
				for f in upload['files']:
					added_data.extend(upload['files'][f]['data'])
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
						"</p><p>".join(map(str,added_data)),#map(lambda x: str(upload['files'][x]['data']),upload['files'])), 
						"".join([upload['files'][x]['display'] for x in upload['files']]) 
						)

			html += '''<a href='/participant/%i/upload'><button>Upload new file<button?</a> ''' % (participant_id, )
		else:
			
			# for key, group in groupby(datapoints, lambda d: d.datatype):
			# 	print key.name
			# 	print group
			# 	data[key.name] = list(group)


			# print datapoints
			# return render_template('dataview.html',
			# 				data=datapoints
			# 			)
			html += '''
				<p>%s</p>
				<h1>Upload new participant file</h1>
				<form action="" method=post enctype=multipart/form-data>
				<p><input type=file name=file multiple>
				<input type=submit value=Upload>
				</form>
				''' % (message,)
			cdn, script, div = bokeh_plot.create_graph(participant_id)
			html += cdn + script + div

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
				'display':'<p>upload: ' + save_path + "</p>",
				'datapoints':[] # format [time, value] (too expensive to create full object!)
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
	participant_id = pending_uploads[hash]['participant_id']
	added_html += "<p>%i files </p>" % (len(pending_uploads[hash]['files']), )
	for upload in pending_uploads[hash]['files'].itervalues():
		added_html += "<p>%i items in file </p>" % (len(upload['data']), )
		for obj in upload['data']:
			if isinstance(obj, Image):
				print obj, " is Image"
				added_html += "<p>" + obj.full_url + "</p" 
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
		if len(upload['datapoints'])>0:
			Datapoint.create_many(upload['datapoints'], participant_id)
			num_datapoints += len(upload['datapoints'])
	# del pending_uploads[hash]
	return render_template('dataview.html')
	return "<a href='/participant/%i'>Go back</a><p>sucessfully added %i images and %i dataponts:</p> %s " % (participant_id, num_images, num_datapoints, added_html)
