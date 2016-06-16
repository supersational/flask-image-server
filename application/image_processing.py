from application import app
import os
import binascii
import PIL
import cgi
from PIL import Image as PILImage 
from io import BytesIO

# uploads
from config import UPLOAD_FOLDER, IMAGE_SIZES



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
	stream = BytesIO()
	im.save(stream, "JPEG")
	try:
		sizeattrs = 'width="%s" height="%s" ' % im.size
	except:
		sizeattrs = ''
	return "<img src='data:image//png;base64,%s' %s alt='%s'\>" % (binascii.b2a_base64(stream.getvalue()), sizeattrs, input_file)


def generate_sizes(input_file, output_path):
	im = PILImage.open(input_file)
	name = file_noextension(input_file)

	for key, size in IMAGE_SIZES.iteritems():
		outfile = os.path.join(output_path, size['dir'], name+".jpg")
		ensure_dir_exists(outfile)
		exists = os.path.isfile(outfile)
		if not exists:
			print("    generating : " + key + " " + str(size['size']) + " " + outfile)
			if size['size'][0]>0 and size['size'][1]>0:
				im_thumb = im.copy()
				im_thumb.thumbnail(size['size'])
				im_thumb.save(outfile,"JPEG")
			else:
				im.save(outfile,"JPEG")

