from application import db
for tbl in reversed(db.metadata.sorted_tables):
	print tbl
	db.engine.execute(tbl.delete())

db.create_db()
