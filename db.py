# coding: utf-8
# from:
# C:\Users\shollowell\Documents\wearable-webapp\python-flask>sqlacodegen postgres://postgres:testing@localhost:3145/linker
import datetime
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
    participant_id = Column(ForeignKey(u'participants.participant_id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    comment = Column(Text)
    number_times_viewed = Column(Integer)

    participant = relationship(u'Participant')
    images = relationship(u'Image')

    def __init__(self, participant_id, start_time, end_time, comment=''):
        self.participant_id = participant_id
        self.start_time = start_time
        self.end_time = end_time
        self.comment = comment
        self.number_times_viewed = 0

    def get_images(self):
        return Image.query.filter((Image.participant_id==self.participant_id) & (Image.image_time <= self.end_time) & (Image.image_time >= self.start_time)).all()

    def tag_images(self):
        if self.event_id:
            for image in self.get_images():
                image.event_id = self.event_id

    def __repr__(self):
        return "Event: %s, %s - %s, participant_id:%s, %s images.\n%s" % (self.event_id, self.start_time, self.end_time, self.participant_id, len(self.images), "\n".join([str(i.image_time) for i in self.images]))

class Image(Base):
    __tablename__ = 'images'

    image_id = Column(Integer, primary_key=True)
    image_time = Column(DateTime, nullable=False)
    participant_id = Column(ForeignKey(u'participants.participant_id'), nullable=False)
    event_id = Column(ForeignKey(u'events.event_id'))
    full_url = Column(String(256))
    medium_url = Column(String(256))
    thumbnail_url = Column(String(256))

    event = relationship(u'Event')
    participant = relationship(u'Participant')

    def __init__(self, participant_id, time, full_url, medium_url, thumbnail_url, event_id=None):
        self.participant_id = participant_id
        self.image_time = time
        self.full_url = full_url
        self.medium_url = medium_url
        self.thumbnail_url = thumbnail_url
        if event_id:
            self.event_id = event_id

    def __repr__(self):
        return str(self.image_time) + " - " + self.full_url + "(" + str(self.participant_id) + ")"
 
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
        txt = 'Participant: %s (id=%s, %s images, ' % (self.name, self.participant_id, len(self.images))
        if len(self.studies)>5:
            return txt + ' in %s studies)' % len(self.studies)
        else:
            return txt + ' studies=%s)' % [x.name for x in self.studies]
    
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
            session.flush() # need to get id
            for s in studies:
                p.studies.append(s)
            full_url = 'http://lorempixel.com/1000/870/animals/'
            med_url = 'http://lorempixel.com/500/435/animals/'
            thum_url = 'http://lorempixel.com/100/87/animals/'
            for j in range(1,20):
                idx = str(j % 10)
                img = Image(p.participant_id, datetime.datetime.today() + datetime.timedelta(seconds=30*j), full_url+idx, med_url+idx, thum_url+idx)
                session.add(img)
            session.flush()
            for k in range(1,5):
                evt = Event(p.participant_id, datetime.datetime.today() + datetime.timedelta(seconds=30*(k)*4),  datetime.datetime.today() + datetime.timedelta(seconds=30*(k+1)*4), )
                session.add(evt)
                print evt
                session.flush()
                evt.tag_images()
                print evt

        p.studies.append(Study('default'))
        print "\n".join(map(str, User.query.all()))
        print "\n".join(map(str, Participant.query.all()))
        print "\n".join(map(str, Study.query.all()))
        t = datetime.datetime.today() + datetime.timedelta(minutes=3)
        print "\n".join(map(str, Image.query.filter(Image.image_time < t).all()))
        print "> " + str(t)
        print "\n".join(map(str, Image.query.filter(Image.image_time > t).all()))

        print "done creating fake data."
        # print loghandler.read()
    return session


if __name__ == "__main__":
    drop_db()
    get_session(create_data=True)
