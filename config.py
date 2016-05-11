import os
# Statement for enabling the development environment
DEBUG = True

#	controls if the cookie should be set with the secure flag. Defaults to False.
SESSION_COOKIE_SECURE = True
# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  

# Define the database - we are working with
# SQLite for this example
SQLALCHEMY_DATABASE_URI = 'postgres://postgres:testing@localhost:5432/linker'
DATABASE_CONNECT_OPTIONS = {}

# TODO:
# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED     = True

# Use a secure, unique and absolutely secret key for
# signing the data. 
CSRF_SESSION_KEY = "secret"

# Node server secret key for hashing image URLs 
NODE_SECRET_KEY = "secret_key_at_least_10_characters"

# Secret key for signing cookies
SECRET_KEY = "secret"

JSONIFY_PRETTYPRINT_REGULAR = False

SERVER_NAME = 'localhost:5000'