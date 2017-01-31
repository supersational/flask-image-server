import os
from application import db
from config import SCHEMA_FOLDER

print "SCHEMA_FOLDER", SCHEMA_FOLDER



for d in os.listdir(SCHEMA_FOLDER):
	if not d.lower().endswith(".csv"):
		continue
	d_full = os.path.join(SCHEMA_FOLDER, d)
	name = d[:-len('.csv')]
	if db.Schema.query.filter(db.Schema.name==name).first() is not None:
		print "schema ",name,"already exists"
	else:
		print "creating schema ", name
		s = db.Schema(name)
		s.from_file(d_full)

		db.session.add(s)
		db.session.flush()
