import psycopg2
import sys
import os

script_folder = os.path.dirname(os.path.realpath(__file__))

def create_cursor():
	global cur
	try:
		cur.close()
	except NameError:
		pass
	cur = conn.cursor()

def get_all_participants():
	cur.execute("""SELECT participant_id, name From Participants""")
	return cur.fetchall()

def get_all_users():
	cur.execute("""SELECT user_id,username,password FROM Users""")
	return cur.fetchall()

def get_user_studies(user_id):
	cur.execute("""SELECT Studies.study_id, Studies.name, UserAccess.access_level FROM Studies 
					INNER JOIN UserAccess ON (UserAccess.user_id = %s AND UserAccess.study_id = Studies.study_id)
					INNER JOIN Users ON UserAccess.user_id = Users.user_id""", [user_id])
	return cur.fetchall()

def add_participant(name):
	if name in [x[1] for x in get_all_participants()]:
		print name, "already exsists"
	cur.execute("""INSERT INTO Participants(participant_id, name) VALUES(default, %s)""", [name])

def add_image(image_time, user_id, full_url, medium_url, thumbnail_url):
	cur.execute("""INSERT INTO Images(image_time, user_id, full_url, medium_url, thumbnail_url, ) VALUES(default, %s)""", [])

def create_db():
	str = ""
	with open('create_db.txt','r') as f:
		txt = f.read()[3:] # remove weird 3  characters at start, bug?
	for command in txt.split(';'):
		try:
			cur.execute(command)
			# print command
		except psycopg2.ProgrammingError:
			print "ProgrammingError\n:Command skipped: ", sys.exc_info(), command
		except psycopg2.InternalError:
			print "InternalError\n:Command skipped: ", sys.exc_info(), command
	conn.commit()

def add_images():
	image_folder = os.path.join(script_folder,'images')
	participants = os.listdir(image_folder)
	print participants
	for p in participants:
		add_participant(p)
		p_dir = os.path.join(image_folder,p)
		for img in os.listdir(os.path.join(p_dir,"full")): # only where we have full resolution
			img_time = parse_img_date(img)
			(full_img, med_img, thumb_img) = map(lambda x: os.path.join('images',p,x,img), ('full', 'medium', 'thumbnail'))
			print "\n".join([full_img, med_img, thumb_img])
			if os.path.isfile(os.path.join(script_folder, full_img)):
				print "good file"
				# add_image(img_time, )
			else:
				print os.path.join(script_folder, full_img)

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
create_cursor()