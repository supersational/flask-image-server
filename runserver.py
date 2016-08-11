from application import app
from config import DEBUG, NODE_SECRET_KEY, NODE_PROCESS, HOST, PORT


import os 
# ensure if debug mode that we only start the node process once (after reboot into debugging mode)
if not DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
	from datetime import datetime
        print '################### Restarting @ {} ###################'.format(
            datetime.utcnow())
	import subprocess
	try:
		NODE_PROCESS = subprocess.Popen(['node', 'application/server.js', NODE_SECRET_KEY], shell=True)
		@app.teardown_appcontext
		def teardown_node(exception):
			if NODE_PROCESS is not None:
				NODE_PROCESS.kill()
	except e:
		print "NODE process failed to start", str(e)

app.run(
	debug=DEBUG, 
	host=HOST,
	port=PORT
	)

