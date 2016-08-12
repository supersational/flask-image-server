from application import app
from config import DEBUG, NODE_SECRET_KEY, HOST, PORT, FLASK_RELOAD


import os 
# ensure if reloading that we only start the node process once (after reboot into debugging mode)
if not FLASK_RELOAD or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
	from datetime import datetime
        print '################### Restarting @ {} ###################'.format(
            datetime.utcnow())
	import subprocess
	@app.teardown_appcontext
	def teardown_nodes(exception):
		if NODE_PROCESS is not None:
			NODE_PROCESS.kill()
		if LOAD_BALANCER is not None:
			LOAD_BALANCER.kill()
	try:
		NODE_PROCESS = subprocess.Popen(['node', 'application/server.js', NODE_SECRET_KEY], shell=True)
	except e:
		print "NODE process failed to start", str(e)
	try:
		LOAD_BALANCER = subprocess.Popen(['node', 'application/load-balancer.js'], shell=True)
	except e:
		print "NODE process failed to start", str(e)
else:
	print "pre-reloading, WERKZEUG_RUN_MAIN=", os.environ.get('WERKZEUG_RUN_MAIN')
	
app.run(
	debug=DEBUG, 
	host=HOST,
	port=PORT,
	use_reloader=FLASK_RELOAD
	)

