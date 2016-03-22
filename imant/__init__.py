# import flask
from flask import Flask
import sys
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object('config')

# for running node server
import imant.run_node
import imant.login
import imant.template_filters
import imant.post
import imant.server