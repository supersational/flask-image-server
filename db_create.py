from application import db
from application import db_data
db_data.create_data(db.session, db.engine)   
