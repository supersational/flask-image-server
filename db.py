# coding: utf-8
# from:
# C:\Users\shollowell\Documents\wearable-webapp\python-flask>sqlacodegen postgres://postgres:testing@localhost:3145/linker

# define database
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
# sqlalchemy errors
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
# create session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


Base = declarative_base()
metadata = Base.metadata
engine = create_engine('postgres://postgres:testing@localhost:5432/linker', convert_unicode=True, logging_name="sqlalchemy.engine")
# logging
import loghandler
loghandler.init("sqlalchemy.engine")

def read_log():
    return loghandler.read()

class Event(Base):
    __tablename__ = 'events'

    event_id = Column(Integer, primary_key=True)
    participant_id = Column(ForeignKey(u'participants.participant_id'))
    day = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    comment = Column(Text)
    number_times_viewed = Column(Integer)

    participant = relationship(u'Participant')


class Image(Base):
    __tablename__ = 'images'

    image_id = Column(Integer, primary_key=True)
    image_time = Column(DateTime)
    participant_id = Column(ForeignKey(u'participants.participant_id'))
    event_id = Column(ForeignKey(u'events.event_id'))
    full_url = Column(String(256))
    medium_url = Column(String(256))
    thumbnail_url = Column(String(256))

    event = relationship(u'Event')
    participant = relationship(u'Participant')


t_studyparticipants = Table(
    'studyparticipants', metadata,
    Column('study_id', Integer, ForeignKey(u'studies.study_id')),
    Column('participant_id', Integer, ForeignKey(u'participants.participant_id')),
    UniqueConstraint('study_id', 'participant_id')
)

class Participant(Base):
    __tablename__ = 'participants'

    participant_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    studies = relationship(u'Study', secondary='studyparticipants')
    images = relationship(u'Image')
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        if len(self.studies)>5:
            return 'Participant: %s (id=%s, in %s studies)' % (self.name, self.participant_id, len(self.studies))
        else:
            return 'Participant: %s (id=%s, studies=%s)' % (self.name, self.participant_id, [x.name for x in self.studies])
    
t_useraccess = Table(
    'useraccess', metadata,
    Column('user_id', Integer, ForeignKey(u'users.user_id')),
    Column('study_id', Integer, ForeignKey(u'studies.study_id')),
    Column('access_level', Integer, nullable=False)
)

class Study(Base):
    __tablename__ = 'studies'

    study_id = Column(Integer, primary_key=True)
    name = Column(String(256))
    participants = relationship(u'Participant', secondary='studyparticipants')
    participants = relationship(u'User', secondary='useraccess')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
            return 'Study: %s (id=%s, participants=%s)' % (self.name, self.study_id, [x.name for x in self.participants])
    


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(50))
    # UniqueConstraint('username')
    studies = relationship(u'Study', secondary='useraccess')

    def __init__(self, username, password):
        # try:
        #     existing = User.query.filter_by(username=username)
        #     raise ValueError("user already exists!")
        # except NoResultFound:
        #     pass

        self.username = username
        self.password = password

    def __repr__(self):
            return 'User: %s (id=%s, password=%s)' % (self.username, self.user_id, '*' * len(self.password))

def drop_db():
    Base.metadata.drop_all(engine)

def create_session(autoflush=True, autocommit=True):
    return scoped_session(sessionmaker(autocommit=autocommit,
                                             autoflush=autoflush,
                                             bind=engine))  
def create_db(drop=False):
    session = create_session()
    Base.metadata.create_all(engine)
    return session

def get_session(create_data=False, run_tests=True):

    # does not actually connect until work is done
    session = create_db()
    Base.query = session.query_property()

    if run_tests:
        tests = {'duplicateUser':False}
        try:
            test_session = create_session(autocommit=False, autoflush=False)
            u = User('Aiden', 'Aiden')
            test_session.add(u)
            u = User('Aiden', 'Aiden2')
            test_session.add(u)
            test_session.flush()
        except IntegrityError:
            print "db rejected duplicate Aiden user, good!"
            test_session.rollback()
            tests['duplicateUser'] = True

        for key, value in tests.iteritems():
            assert value, key + " test failed!" 
        if all(value == True for value in tests.values()):
            print "all %s tests passed" % len(tests)

    if create_data:
        u = User('Aiden', 'Aiden')
        if len(User.query.filter(User.username==u.username).all())==0:
            session.add(u)
        if len(User.query.filter(User.username==u.username).all())==0:
            session.add(u)
        u = User('Testing', '')
        if len(User.query.filter(User.username==u.username).all())==0:
            session.add(u)
        studies = []
        for i in range(1,20):
            s = Study("S" + str(i))
            session.add(s)
            studies.append(s)
            p = Participant("P" + str(i))
            session.add(p)
            for s in studies:
                p.studies.append(s)

        
        p.studies.append(Study('default'))
        print "\n".join(map(str, User.query.all()))
        print "\n".join(map(str, Participant.query.all()))
        print "\n".join(map(str, Study.query.all()))
        print "done creating fake data."
        # print loghandler.read()
    return session


if __name__ == "__main__":
    drop_db()
    get_session(create_data=True)
