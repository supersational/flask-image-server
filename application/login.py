from application import app
from flask import request, redirect, url_for
from flask import render_template
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
from application.db import User, Study, Participant
from functools import wraps

login_manager = LoginManager()
login_manager.init_app(app)
# Login handling
@login_manager.user_loader
def load_user(id):
	return User.query.get(int(id))

# automatically checks for user access to study_id, participant_id, or user_id (all specified by <int:study_id> etc. in kwargs)
def login_check():
	def true_decorator(f):
		@wraps(f)
		def wrapper(*args, **kwargs):
			# print "wrapper"
			# print args, kwargs
			# print current_user
			if not current_user:
				return render_template('login.html', message="You must be logged in to view this page")
			if current_user.admin is True:
				return f(*args, **kwargs)

			if 'study_id' in kwargs:
				print 'study_id ', kwargs['study_id']
				if not Study.query.filter(Study.study_id==kwargs['study_id']).one() in current_user.studies:
					return render_template('login.html', message="You do not have access to this study")
			if 'participant_id' in kwargs:
				print 'participant_id ', kwargs['participant_id']
				if not Participant.query.filter(Participant.participant_id==kwargs['participant_id']).one() in \
					[study.participants for study in current_user.studies]:
					return render_template('login.html', message="You do not have access to this participant")
			if 'user_id' in kwargs:
				print 'user_id ', kwargs['user_id']
				if not User.query.filter(User.user_id==kwargs['user_id']).one()==current_user:
					return render_template('login.html', message="You may only view your own user page", link_href="/user/"+str(current_user.user_id), link_message="Click here for your user page")
			return f(*args, **kwargs)
		return wrapper
	return true_decorator

def requires_admin(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		if current_user and current_user.admin is True:
			return f(*args, **kwargs)
		return render_template('login.html', message="You must be an administrator view this page")
	return wrapper

login_manager.login_view = 'login'
@app.route('/login', methods=['GET', 'POST'])
def login():

	if request.method == 'GET':
		return render_template('login.html')

	username = request.form['username']
	password = request.form['password']
	if request.form['url'] and request.form['url']!='/login':
		url  = request.form['url']
	else:
		url = '/' 
	registered_user = User.query.filter_by(username=username).first()
	print registered_user
	print request.endpoint
	if registered_user is None:
		return render_template('login.html', message="error: incorrect username")
	elif not registered_user.check_password(password):
		return render_template('login.html', message="error: incorrect password")
	elif login_user(registered_user, remember=True):
		return redirect(url)
	else:
		return render_template('login.html', message="error: in login_user")

@app.route('/logout')
@login_required
def logout():
	print request.url
	logout_user()
	return redirect('/')

@login_manager.unauthorized_handler
def unauthorized():
	return render_template('login.html', message="This page requires login!")