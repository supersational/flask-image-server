from application import app
import os
import binascii
import PIL
import cgi
from PIL import Image as PILImage 
# from io import BytesIO
from StringIO import StringIO

# uploads
from config import UPLOAD_FOLDER, IMAGE_SIZES, IMAGES_FOLDER, IMAGES_FOLDER_NAME



IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
def file_extension(filename):
	return '' if '.' not in filename else filename.rsplit('.', 1)[1].lower()

def file_noextension(filename):
	return os.path.splitext(os.path.basename(filename))[0]

def ensure_dir_exists(directory):
	# print os.path.dirname(directory), os.path.exists(os.path.dirname(directory))
	if not os.path.isdir(os.path.dirname(directory)):
		os.makedirs(os.path.dirname(directory))

def to_html_img(input_file, size=None):
	im = PILImage.open(input_file)
	if size is not None:
		im = im.copy()
		im.thumbnail(size)
	else: return "img size was None!"
	print "im.size", im.size
	stream = StringIO()
	im.save(stream, "JPEG")
	try:
		sizeattrs = 'width="%s" height="%s" ' % im.size
	except:
		sizeattrs = ''
	return "<img src='data:image//png;base64,%s' %s alt='%s'\>" % (binascii.b2a_base64(stream.getvalue()), sizeattrs, input_file)


def generate_sizes(input_file, participant_id, overwrite=True):
	im = PILImage.open(input_file)
	name = file_noextension(input_file)
	output_files = {}
	for key, size in IMAGE_SIZES.iteritems():
		outfile_full = os.path.join(IMAGES_FOLDER, str(participant_id), size['dir'], name+".jpg")
		outfile = '/'+os.path.join(IMAGES_FOLDER_NAME, str(participant_id), size['dir'], name+".jpg")

		ensure_dir_exists(outfile_full)
		exists = os.path.isfile(outfile_full)
		if not exists or overwrite:
			print("    generating : " + key + " " + str(size['size']) + " " + outfile +" curr size:" + str(im.size))

			# if a size is specified, then resize
			if size['size'][0]>0 and size['size'][1]>0:
				im_thumb = im.copy()
				im_thumb.thumbnail(size['size'])
				im_thumb.save(outfile_full,"JPEG")
			else:
				# full resolution
				im.save(outfile_full,"JPEG")
			# store file location for each size
			output_files[key] = outfile
		else:
			output_files[key] = None
	return output_files