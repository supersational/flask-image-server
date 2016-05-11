# import flask
from flask import Flask
import sys
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object('config')

# for running node server
import application.run_node
import application.login
import application.template_filters
import application.post
import application.server