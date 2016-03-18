# import flask
from flask import Flask

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object('config')

import imant.server
    
# if __name__ == "__main__":
# 	# import subprocess, os
# 	print "running on port 5000"
# 	app.config["SECRET_KEY"] = "secret? what's that?"
# 	app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
  
# 	app.run(port=5000, debug=True)
# 	# app = ProfilerMiddleware(app)
