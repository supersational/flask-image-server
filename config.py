import os
import uuid

#	controls if the cookie should be set with the secure flag. Defaults to False.
SESSION_COOKIE_SECURE = True
# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  

# Define the database - we are working with
# SQLite for this example
SQLALCHEMY_DATABASE_URI = 'postgres://postgres:testing@localhost:5432/linker'
if 'SQLALCHEMY_DATABASE_URI' in os.environ:
	SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']

# if we are in a docker containter use the env variables set for that purpose
if all(val in os.environ for val in ['POSTGRES_ENV_POSTGRES_PASSWORD','POSTGRES_PORT']):
	pg_host = os.environ['POSTGRES_PORT']
	if pg_host.startswith('tcp://'):
		pg_host=pg_host[len('tcp://'):]
	SQLALCHEMY_DATABASE_URI = 'postgres://postgres:%s@%s/linker' % (os.environ['POSTGRES_ENV_POSTGRES_PASSWORD'],pg_host)
# SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///'+os.path.join(BASE_DIR,'app.db')
DATABASE_CONNECT_OPTIONS = {}

# TODO:
# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED     = True

# Use a secure, unique and absolutely secret key for
# signing the data. 
CSRF_SESSION_KEY = "secret"


JSONIFY_PRETTYPRINT_REGULAR = False

PORT = 5000
HOST = 'localhost'
DEBUG = True
if 'FLASK_DEBUG_DISABLE' in os.environ:
	DEBUG=False
LOGGING = False
FLASK_RELOAD = True
if 'FLASK_RELOAD_DISABLE' in os.environ:
	FLASK_RELOAD=False

APPLICATION_FOLDER =os.path.join(BASE_DIR, "application")
IMAGES_FOLDER_NAME = "images"
IMAGES_FOLDER =os.path.join(BASE_DIR, "application", IMAGES_FOLDER_NAME)
UPLOAD_FOLDER =os.path.join(BASE_DIR, "application", "upload_folder")
SCHEMA_FOLDER = os.path.join(BASE_DIR, "application", "annotation")

# Secret key for signing cookies
SECRET_KEY = "constant so we don't have to login every time" if DEBUG is True else uuid.uuid4().hex
print "SECRET_KEY", SECRET_KEY
# Node server secret key for hashing image URLs 
NODE_SECRET_KEY = "node secret key" if DEBUG else uuid.uuid4().hex

SUPPORTED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
SUPPORTED_DATA_EXTENSIONS = ["csv"]

IMAGE_SIZES = {
	'thumbnail':{'size':(100, 100),'dir':'thumbnail'},
	'medium':{'size':(864, 645),'dir':'medium'},
	'full':{'size':(0, 0),'dir':'full'}
}

