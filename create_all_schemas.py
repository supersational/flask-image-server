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
		db.session.delete(db.Schema.query.filter(db.Schema.name==name).first())
		db.session.flush()
	# else:
	print "creating schema ", name
	s = db.Schema(name)
	db.session.add(s)
	db.session.flush()
	s.from_file(d_full)
	db.session.flush()
	print s
	print s
	print s.dump()