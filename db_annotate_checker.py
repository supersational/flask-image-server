from application import db
from application import db_data
import os
import datetime
import csv

def get_P(file_name):
	file_name = os.path.basename(file_name) # remove folder from path
	if file_name.lower().startswith("p") and all(map(str.isdigit, file_name[1:4])):
		return int(file_name[1:4])
	else:
		return -1
 

# get list of Angel annotation files
ANNOTATION_FOLDER = "T:\\Data\\Annotated participants files\\Main annotation Angel\\imageLevel (csv files from SQLite SplitBrower"
annotation_files = {}
for f in os.listdir(ANNOTATION_FOLDER):
	P = get_P(f)
	# print f, P
	if f.endswith(".csv") and P!=-1 and not (P in annotation_files and len(f) < len(annotation_files[P]) ):
		annotation_files[P] = f
print "FOUND annotation_files", len(annotation_files)

# find main Schema
main_schema = None
for s in db.Schema.query.all():
	print s
	if s.name == 'main-annotation-schema':
		main_schema = s
if main_schema is None:
	sys.exit()

def label_repr(l):
	name = l.folder.name + ';' +l.name
	l = l.folder
	while l.parent and l.parent is not None:
		l = l.parent
		name = l.name + ';' + name
	return name.strip()

# print all Schema labels
labels = {}
for l in main_schema.labels:
	name = label_repr(l)
	# print name
	labels[name] = l

# methods to find labels where there is not an exact match
from difflib import SequenceMatcher
def similar(a, b):
	return SequenceMatcher(None, a, b).ratio()

def find_closest(t):
	if len(t)<1:
		return None
	print "    " + t
	best = -1
	best_result = None
	for key, value in labels.iteritems():
		s = similar(t, key)
		if s > best:
			best = s
			best_result = labels[key]
	print best, " -> ",best_result
	if best_result!=None:
		labels[t] = best_result
	return best_result
	# TODO: error if below a match threshold
	
show_good = False
not_found = set([])
not_eliminated = set([])
def read_image_annotations(fname):
	with open(fname) as f:
		n = 0
		for l in f:
			n += 1
			if n < 2:
				continue # skip first two lines

			date = l.split(',')[1]
			# if fname.endswith("p002_AngelWong_correction.csv"):
				#23/01/1991 08:02,
			for dformat in ["%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S","%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M"]:
				try:
					date = datetime.datetime.strptime(date, dformat)
					break
				except ValueError:
					continue
			if type(date) == str:
				raise ValueError(date + " is not in a valid format")
			# print date
			annotation = l.split(',')[2].strip()
			if len(annotation)<1:
				continue
			num_chars = len(annotation)
			matches = [labels[x] for x in labels if x[:num_chars]==annotation]

			if len(matches)==1:
				label = matches[0]
			else:
				label = find_closest(annotation)

			if label is None:
				print "WARNING: ", annotation
				continue
			yield [date, label, annotation]

img_length = datetime.timedelta(seconds=60)
sec = datetime.timedelta(seconds=1)
# read all Angel annotations
for P in db.Participant.query.all():
	print "working on Participant:", P.name
	P_num = get_P(str(P.name))
	print P_num
	if P_num in annotation_files:
		f = annotation_files[P_num]
		print "found file : " , f
		curr_event = None
		curr_label = None
		last_eventtime = None
		for e in P.events:
			db.session.delete(e)
		for date, label, annotation in read_image_annotations(os.path.join(ANNOTATION_FOLDER, f)):
			if not label or not label.label_id or label.label_id is None:
				continue
				
			print date, label.label_id, annotation
			# continue 
			if curr_event is not None:
				if curr_label is None or label.label_id == curr_label.label_id:
					curr_event.end_time = date+img_length- sec
				else:
					curr_event.end_time = min(date-sec*2, curr_event.end_time)
					db.session.add(curr_event)
					curr_event.tag_images()
					db.session.flush()
					print "start:", curr_event.start_time, " imgs:", len(curr_event.get_images()), ", ", len(curr_event.images)
					curr_event = db.Event(P.participant_id, date-sec, date+img_length, comment='', label_id=label.label_id)
					
			# 	if (date - last_eventtime > img_length):
			# 		curr_event.
			if curr_event is None:
				curr_event = db.Event(P.participant_id, date-sec*2, date+img_length, comment='', label_id=label.label_id)
			curr_label = label
			# print annotation
print "\nnot_eliminated:", len(not_eliminated)
print "\n".join(not_eliminated)
print "\nnot_found:", len(not_found)
print "\n".join(not_found)
