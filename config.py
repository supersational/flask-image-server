import os
import uuid

# Statement for enabling the development environment
DEBUG = True

#	controls if the cookie should be set with the secure flag. Defaults to False.
SESSION_COOKIE_SECURE = True
# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  

# Define the database - we are working with
# SQLite for this example
SQLALCHEMY_DATABASE_URI = 'postgres://postgres:testing@localhost:5432/linker'
# SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///'+os.path.join(BASE_DIR,'app.db')
DATABASE_CONNECT_OPTIONS = {}

# TODO:
# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED     = True

# Use a secure, unique and absolutely secret key for
# signing the data. 
CSRF_SESSION_KEY = "secret"

# Node server secret key for hashing image URLs 
NODE_SECRET_KEY = uuid.uuid4().hex
# Ref to node process so we can kill it
NODE_PROCESS = None


# Secret key for signing cookies
SECRET_KEY = "constant so we don't have to login every time"
print "SECRET_KEY", SECRET_KEY
JSONIFY_PRETTYPRINT_REGULAR = False

PORT = 5000
SERVER_NAME = 'localhost:' + str(PORT)
DEBUG = True
LOGGING = False

APPLICATION_FOLDER =os.path.join(BASE_DIR, "application")
IMAGES_FOLDER =os.path.join(BASE_DIR, "application", "images")
UPLOAD_FOLDER =os.path.join(BASE_DIR, "application", "upload_folder")

SUPPORTED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
SUPPORTED_DATA_EXTENSIONS = ["csv"]

IMAGE_SIZES = {
	'thumbnail':{'size':(100, 100),'dir':'thumbnail'},
	'medium':{'size':(864, 645),'dir':'medium'},
	'full':{'size':(0, 0),'dir':'full'}
}

if 'USER' in os.environ and os.environ['USER']=='sensors':
	# http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
	import socket
	ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
	print 'production server running on ', ip
	SERVER_NAME = ip + ':' + str(PORT)
	print SERVER_NAME
	SQLALCHEMY_DATABASE_URI = 'postgres:///sensors'
	DEBUG = False
	SECRET_KEY = uuid.uuid4().hex