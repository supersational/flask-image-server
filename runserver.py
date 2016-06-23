from application import app
from config import DEBUG

app.run(
	debug=DEBUG, 
	host='0.0.0.0' if not DEBUG else None # do not all external access if debug is enabled
	)
