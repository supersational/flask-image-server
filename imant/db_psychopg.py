import psycopg2
from psycopg2 import IntegrityError
from psycopg2.extras import NamedTupleConnection
import sys
import os
from datetime import date
script_folder = os.path.dirname(os.path.realpath(__file__))

import automatic_sqlacodegen as tables
from flask_sqlalchemy import SQLAlchemy




def create_cursor():
	global cur
	try:
		cur.close()
	except NameError:
		pass
	cur = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

def get_studies(study_id=None):
	if study_id is not None:
		cur.execute("""SELECT study_id, name FROM Studies WHERE study_id=%s""", [study_id])
	else:
		cur.execute("""SELECT study_id, name FROM Studies""")
	return cur.fetchall()


def get_studyparticipants(study_id=None, participant_id=None):
	if study_id is not None and participant_id is not None:
		cur.execute("""SELECT * FROM StudyParticipants WHERE (study_id=%s AND participant_id=%s)""", [study_id, participant_id])
	elif study_id is not None:
		cur.execute("""SELECT * FROM StudyParticipants WHERE study_id=%s""", [study_id])
	elif participant_id is not None:
		cur.execute("""SELECT * FROM StudyParticipants WHERE participant_id=%s""", [participant_id])
	else:
		cur.execute("""SELECT * FROM StudyParticipants""")
	return cur.fetchall()

def add_studyparticipant(study_id, participant_id):
	try:
		cur.execute("""INSERT INTO StudyParticipants(study_id, participant_id) VALUES(%s, %s)""", [study_id, participant_id])
		return True
	except IntegrityError:
		print "adding study - participant (%s, %s) link failed: already exists!" % (study_id, participant_id)
		return False

def remove_studyparticipant(study_id, participant_id):
	cur.execute("""DELETE FROM StudyParticipants WHERE (study_id=%s AND participant_id=%s)""", [study_id, participant_id])

def get_participants(participant_id=None, study_id=None):
	command = """SELECT Participants.participant_id, Participants.name FROM Participants"""
	if participant_id is not None:
		command += cur.mogrify(""" WHERE Participants.participant_id=%s""",[participant_id])
	
	if study_id is not None:
		command += cur.mogrify(""" INNER JOIN StudyParticipants ON (Participants.participant_id=StudyParticipants.participant_id AND StudyParticipants.study_id=%s)""",[study_id])
	print command
	cur.execute(command)
	return cur.fetchall()

def get_participant_days(participant_id):
	cur.execute("""SELECT image_time FROM Images WHERE Images.participant_id=%s""", [participant_id])
	data =  [x[0] for x in cur.fetchall()]

	unique_days = {}
	for time in data:
		day = str(date(time.year,time.month,time.day))
		hour = time.hour
		if day in unique_days:
			if hour in unique_days[day]:
				unique_days[day][hour] += 1
			else: unique_days[day][hour] = 1
		else: 
			unique_days[day] = {}
			unique_days[day][hour] = 1

	# for day in unique_days:
	# 	print day
	# 	for hour in unique_days[day]:
	# 		print day, "- " + str(hour) + ":00 : ", unique_days[day][hour], " images"

	return unique_days

def get_users(user_id=None):
	command = """SELECT user_id,username,password FROM Users"""
	if user_id is not None:
		command += cur.mogrify(" WHERE user_id=%s", user_id)
	cur.execute(command)
	return cur.fetchall()

def get_user_studies(user_id):
	cur.execute("""SELECT Studies.study_id, Studies.name, UserAccess.access_level FROM Studies 
					INNER JOIN UserAccess ON (UserAccess.user_id = %s AND UserAccess.study_id = Studies.study_id)
					INNER JOIN Users ON UserAccess.user_id = Users.user_id""", [user_id])
	return cur.fetchall()

def add_participant(name):
	if name in [x[1] for x in get_participants()]:
		print name, "already exsists"
	cur.execute("""INSERT INTO Participants(participant_id, name) VALUES(default, %s) RETURNING participant_id""", [name])
	try:
		return cur.fetchone()[0]
	except NameError:
		return None

def get_images(participant_id=None, only_number=False, date_range=None, event_id=None):
	cmd = """SELECT * FROM Images"""
	if only_number:
		cmd = """SELECT COUNT(*) FROM Images"""
	date_where = ""
	if date_range is not None:
		date_where = cur.mogrify("""image_time BETWEEN %s AND %s """, [date_range['min'],date_range['max']])
		print date_where

	event_where = ""
	if event_id is not None:
		event_where = cur.mogrify(""" event_id = %s """, [date_range['min'],date_range['max']])
		print event_where

	
	if participant_id is not None: # check it's an integer
		if len(date_where)>0:
			date_where = " AND " + date_where
		cur.execute(cmd + """ WHERE (participant_id=%s """ + date_where + ")", [str(participant_id)])
	else:
		if len(date_where) > 0:
			cur.execute(cmd + """ WHERE """ + date_where)
		else:
			cur.execute(cmd)
	if only_number:
		return cur.fetchone()[0]
	else:
		return cur.fetchall()

def add_image(image_time, participant_id, full_url, medium_url, thumbnail_url):
	cur.execute("""INSERT INTO Images(image_time, participant_id, full_url, medium_url, thumbnail_url) VALUES(%s, %s, %s, %s, %s)""", [image_time, participant_id, full_url, medium_url, thumbnail_url])

def add_images(image_array):
	"""quick way to bulk add images into the db (all compressed into a single query)"""
	args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s)", x) for x in image_array)
	cur.execute("""INSERT INTO Images(image_time, participant_id, event_id, full_url, medium_url, thumbnail_url) VALUES """ + args_str)

def load_images():
	image_array = []
	image_folder = os.path.join(script_folder,'images')
	participants = os.listdir(image_folder)
	print participants
	for p in participants:
		participant_id = add_participant(p)
		print "created participant " + str(p) + " id: " + str(participant_id)
		if participant_id is not None:
			p_dir = os.path.join(image_folder,p)
			for img in os.listdir(os.path.join(p_dir,"full")): # only where we have full resolution
				img_time = parse_img_date(img)
				(full_img, med_img, thumb_img) = map(lambda x: os.path.join('images',p,x,img), ('full', 'medium', 'thumbnail'))
				# print "\n".join([full_img, med_img, thumb_img])
				if os.path.isfile(os.path.join(script_folder, full_img)):
					# print "good file"
					image_array.append((img_time, participant_id, None, full_img, med_img, thumb_img))
				else:
					print os.path.join(script_folder, full_img)
			add_studyparticipant(4, participant_id)
	return image_array

def parse_img_date(n):
	"""parse a date from the image filename e.g. B00000000_21I51Q_20140623_105210E.jpg"""
	return "".join([
        n[17:21]+"-", # year
        n[21:23]+"-", # month
        n[23:25]+" ", # day
        n[26:28]+":", # hour
        n[28:30]+":", # minutes
        n[30:32]+".", # seconds
        n[6:9] # this is the photo's sequence number, used as a tiebreaker millisecond value for photos with the same timestamp 
       ])

def create_db(and_add_images=False):
	str = ""
	with open('create_db.txt','r') as f:
		txt = f.read()[3:] # remove weird 3  characters at start, bug?
	for command in txt.split(';'):
		print command
		try:
			cur.execute(command)
			# print command
		except psycopg2.ProgrammingError:
			print "ProgrammingError\n:Command skipped: ", sys.exc_info(), command
		except psycopg2.InternalError:
			print "InternalError\n:Command skipped: ", sys.exc_info(), command

	if add_images:
		images = load_images()
		print images[0]
		add_images(images)
	return txt
	
conn = psycopg2.connect("dbname='linker' user='postgres' host='localhost' password='testing' port='3145'")
conn.autocommit = True
create_cursor()