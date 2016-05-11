import os, sys
from PIL import Image
from time import sleep
import collections 
def create_folder(folder): 
	if not os.path.exists(os.path.dirname(folder)):
	    try:
	        os.makedirs(os.path.dirname(folder))
	    except OSError as exc: # Guard against race condition
	        if exc.errno != errno.EEXIST:
	            raise
	return folder

sizes = {
	'thumbnail':{'size':(100, 100),'dir':'thumbnail'},
	'medium':{'size':(864, 645),'dir':'medium'},
	'full':{'size':(0, 0),'dir':'full'}
}
sizes = collections.OrderedDict(sorted(sizes.items(), key=lambda x: x)) # order alphabetically

verbose = False
overwrite = True
output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),'application', 'images')
participant_dir = 'C:\\Users\\shollowell\\Documents\\wearable_image_data'
# participant_dir = 'T:\\Data\\Main'
allsubdirs = [x for x in os.listdir(participant_dir) if os.path.isdir(os.path.join(participant_dir,x))]
create_folder(participant_dir)

print output_folder

for folder in allsubdirs:
	print folder
	# copy participant folder 
	output_subfolder = create_folder(os.path.join(output_folder, folder))
	input_folder = os.path.join(participant_dir,folder)
	print("getting all images from " + input_folder)
	allfiles = [os.path.join(dp, f) for dp, dn, filenames in os.walk(input_folder) for f in filenames if not os.path.isdir(f)]
	imgfiles = [x for x in allfiles if (os.path.splitext(x)[-1].lower() in [".jpg",".jpeg"])] # filter from allfiles if extension matches
	print ("found " + str(len(imgfiles)) + " imgfiles")

	if len(imgfiles)==0:
		continue
	print str(imgfiles[0])
	for imgfile in imgfiles:
		fullpath = os.path.join(input_folder, imgfile)
		if verbose: print("-found jpg: " + imgfile)
		try:
			im = Image.open(fullpath)
			for key, size in sizes.iteritems():
				outfile = os.path.join(output_subfolder, size['dir'], os.path.splitext(os.path.basename(imgfile))[0] + ".jpg")
				create_folder(os.path.realpath(outfile))
				print size['dir'], outfile
				# sleep(0.01)
				exists = os.path.isfile(outfile)
				if overwrite or (not exists):
					if verbose: print("    generating : " + key + " " + str(size) + " " + outfile)
					if size['size'][0]>0 and size['size'][1]>0:
						im.thumbnail(size['size'])
					im.save(outfile,"JPEG")
				elif (verbose or 1) and (not exists): 
					print("    file exists : " + key + " " + outfile)

		except IOError:
			print("    cannot resize " + imgfile)
