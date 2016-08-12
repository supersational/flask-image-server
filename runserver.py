import config
# change config node key based on command line parameters (will be supplied by load-balancer)
import sys 
print sys.argv
if len(sys.argv) > 1:
	print "key = ", sys.argv[1], "len = ", len(sys.argv[1])
	config.NODE_SECRET_KEY = sys.argv[1]

# import app after so it uses correct key
from application import app

app.run(
	debug=config.DEBUG, 
	host=config.HOST,
	port=config.PORT,
	use_reloader=config.FLASK_RELOAD
	)

