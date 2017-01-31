import os, sys, random
from application import db, file_upload
from config import IMAGES_FOLDER, APPLICATION_FOLDER
import sqlalchemy
import shutil
from application.image_processing import IMAGE_EXTENSIONS, file_extension

def create_or_get_participant(name):
	try:
		return db.Participant.query.filter(db.Participant.name==name).one()
	except sqlalchemy.orm.exc.NoResultFound:
		p = db.Participant(name)
		db.session.add(p)
		db.session.flush()
		return p
print "IMAGES_FOLDER", IMAGES_FOLDER
print "APPLICATION_FOLDER", APPLICATION_FOLDER



for d in os.listdir(IMAGES_FOLDER):
	d_full = os.path.join(IMAGES_FOLDER, d)
	print "D =",d_full
	if os.path.isdir(d_full):
		print d
		try:
			d_int = int(d)
			p = db.Participant.query.get(d_int)
		except Exception as e:
			print e
			p = None
		if p is None:
			p = db.Participant("Auto-created ("+str(d)+")")
			db.session.add(p)
			db.session.flush()
			print "moving:", d_full, " to "
			print p
			print p.get_image_folder()
			shutil.move(d_full, p.get_image_folder())
		print "Pariticipant - ", str(p.name)
		p_image_folder = p.get_image_folder()
		print "p_image_folder=", p_image_folder
		p_thumbnail_folder = os.path.join(p_image_folder, "thumbnail")
		print "p_thumbnail_folder=", p_thumbnail_folder
		p_medium_folder = os.path.join(p_image_folder, "medium")
		print "p_medium_folder=", p_medium_folder
		p_full_folder = os.path.join(p_image_folder, "full")
		print "p_full_folder=", p_full_folder

		p_images = p.images.all()
		p_image_paths = [img.full_url.lower() for img in p_images]
		print p_image_paths

		for walkdir in os.walk(p.get_image_folder()):
			# print walkdir
			if walkdir[0].startswith(p_thumbnail_folder) or  walkdir[0].startswith(p_medium_folder):
				print "skipping dir:", walkdir[0]
				continue
			print "not skipping dir: ", walkdir[0]
			for img in walkdir[2]:
				if file_extension(img) in IMAGE_EXTENSIONS:
					img_path = os.path.join(walkdir[0],img)
					# print "  ",img
					# print "  ",os.path.join(IMAGES_FOLDER, img)
					img_path_rel = os.path.relpath(img_path, start=APPLICATION_FOLDER)
					if "/"+img_path_rel.lower() in p_image_paths:
						print "  img is loaded:", img_path
					else:
						print "  img doesn't exist:", img_path 
						print "  - creating from ", os.path.join(APPLICATION_FOLDER, img_path)
						try:
							os.mkdir(p_full_folder)
						except:
							pass
						try:
							print os.path.join(APPLICATION_FOLDER, img_path), " \n -> ", os.path.join(p_full_folder, img)
							shutil.move(os.path.join(APPLICATION_FOLDER, img_path), os.path.join(p_full_folder, img))
						except Exception as e:
							print e
						new_img = db.Image.from_file(os.path.join(p_full_folder, img), p.participant_id)
						p.images.append(new_img)	
						p_image_paths.append(new_img.full_url.lower())