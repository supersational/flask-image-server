import psycopg2
from psycopg2 import IntegrityError
from psycopg2.extras import NamedTupleConnection
import sys
import os

script_folder = os.path.dirname(os.path.realpath(__file__))

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

def get_images(participant_id=None, only_number=False):
	if only_number:
		cur.execute("""SELECT COUNT(*) FROM Images""")
		return cur.fetchone()[0]
	else:
		if participant_id is not None: # check it's an integer
			cur.execute("""SELECT * FROM Images WHERE participant_id=%s""", [str(participant_id)])
		else:
			cur.execute("""SELECT * FROM Images""")
		return cur.fetchall()

def add_image(image_time, participant_id, full_url, medium_url, thumbnail_url):
	cur.execute("""INSERT INTO Images(image_time, participant_id, full_url, medium_url, thumbnail_url) VALUES(%s, %s, %s, %s, %s)""", [image_time, participant_id, full_url, medium_url, thumbnail_url])
	# conn.commit()

def add_images(image_array):
	args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s)", x) for x in image_array)
	print "len:", len(args_str)
	print
	print args_str[:500]
	print
	print args_str[-500:]
	cur.execute("""INSERT INTO Images(image_time, participant_id, full_url, medium_url, thumbnail_url) VALUES """ + args_str)
	# conn.commit()

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
	# conn.commit()

	if add_images:
		images = load_images()
		print images[0]
		add_images(images)
	return txt

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
					image_array.append((img_time, participant_id, full_img, med_img, thumb_img))
					# add_image(img_time, )
				else:
					print os.path.join(script_folder, full_img)
			add_studyparticipant(4, participant_id)
	return image_array

def parse_img_date(n):
	return "".join([
        n[17:21]+"-", # year
        n[21:23]+"-", # month
        n[23:25]+" ", # day
        n[26:28]+":", # hour
        n[28:30]+":", # minutes
        n[30:32]+".", # seconds
        n[6:9] # this is the photo's sequence number, used as a tiebreaker millisecond value for photos with the same timestamp 
       ])
	
conn = psycopg2.connect("dbname='linker' user='postgres' host='localhost' password='testing' port='3145'")
conn.autocommit = True
create_cursor()