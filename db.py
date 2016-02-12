# coding: utf-8
# from:
# C:\Users\shollowell\Documents\wearable-webapp\python-flask>sqlacodegen postgres://postgres:testing@localhost:3145/linker

# define database
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
# create session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


Base = declarative_base()
metadata = Base.metadata
engine = create_engine('postgres://postgres:testing@localhost:5432/linker', convert_unicode=True)#, echo=True)


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

    def __init__(self, name):
        self.name = name

    def __repr__(self):
            return 'Participant: %s (id=%s, studies=%s)' % (self.name, self.participant_id, [x.name for x in self.studies])
    

class Study(Base):
    __tablename__ = 'studies'

    study_id = Column(Integer, primary_key=True)
    name = Column(String(256))
    participants = relationship(u'Participant', secondary='studyparticipants')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
            return 'Study: %s (id=%s, participants=%s)' % (self.name, self.study_id, [x.name for x in self.participants])
    
t_useraccess = Table(
    'useraccess', metadata,
    Column('user_id', ForeignKey(u'users.user_id')),
    Column('study_id', ForeignKey(u'studies.study_id')),
    Column('access_level', Integer, nullable=False)
)


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(50))
    password = Column(String(50))
    UniqueConstraint('username')

    def __init__(self, username, password):
        try:
            existing = User.query.filter_by(username=username)
            raise ValueError("user already exists!")
        except NoResultFound:
            pass

        self.username = username
        self.password = password

    def __repr__(self):
            return 'User: %s (id=%s, password=%s)' % (self.username, self.user_id, '*' * len(self.password))

def create_db(drop=False):
    if drop:
        Base.metadata.drop_all(engine)
    session = scoped_session(sessionmaker(autocommit=True,
                                             autoflush=True,
                                             bind=engine))
    Base.metadata.create_all(engine)
    return session

def get_session(run_tests=False):

    # does not actually connect until work is done
    session = create_db()
    Base.query = session.query_property()
    if run_tests:
        # this should error if 
        # u = User('Aiden', 'Aiden')
        # session.add(u)
        print "\n".join(map(str, User.query.all()))
        p = Participant('hi')
        session.add(p)
        p.studies.append(Study('histudy'))
        print "\n".join(map(str, Participant.query.all()))
        print "\n".join(map(str, Study.query.all()))
        p1 = Participant.query.first()
        print len(p1.studies)
        print "ran tests"
    return session


if __name__ == "__main__":
    get_session(run_tests=True)
