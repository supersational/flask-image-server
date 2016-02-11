# coding: utf-8
# from:
# C:\Users\shollowell\Documents\wearable-webapp\python-flask>sqlacodegen postgres://postgres:testing@localhost:3145/linker

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class Event(Base):
    __tablename__ = 'events'

    event_id = Column(Integer, primary_key=True, server_default=text("nextval('events_event_id_seq'::regclass)"))
    participant_id = Column(ForeignKey(u'participants.participant_id'))
    day = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    comment = Column(Text)
    number_times_viewed = Column(Integer)

    participant = relationship(u'Participant')


class Image(Base):
    __tablename__ = 'images'

    image_id = Column(Integer, primary_key=True, server_default=text("nextval('images_image_id_seq'::regclass)"))
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

    participant_id = Column(Integer, primary_key=True, server_default=text("nextval('participants_participant_id_seq'::regclass)"))
    name = Column(String(50), nullable=False)

    studies = relationship(u'Study', secondary='studyparticipants')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
            return 'Participant: %s (id=%s, studies=%s)' % (self.name, self.participant_id, [x.name for x in self.studies])
    

class Study(Base):
    __tablename__ = 'studies'

    study_id = Column(Integer, primary_key=True, server_default=text("nextval('studies_study_id_seq'::regclass)"))
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

    user_id = Column(Integer, primary_key=True, server_default=text("nextval('users_user_id_seq'::regclass)"))
    username = Column(String(50))
    password = Column(String(50))
    newprop = Column(String(10))
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
            return 'User: %s (id=%s, password=%s)' % (self.username, self.user_id, '*' * len(self.password))
    
if __name__ == "__main__":


    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    # does not actually connect until work is done
    engine = create_engine('postgres://postgres:testing@localhost:3145/linker', convert_unicode=True)#, echo=True)
    db_session = scoped_session(sessionmaker(autocommit=True,
                                             autoflush=True,
                                             bind=engine))
    Base.metadata.create_all(bind=engine)
    Base.query = db_session.query_property()

    u = User('Supa', 'Aiden')
    db_session.add(u)
    print "\n".join(map(str, User.query.all()))
    p = Participant('hi')
    db_session.add(p)
    p.studies.append(Study('histudy'))
    # db_session.update(p)
    print "\n".join(map(str, Participant.query.all()))
    print "\n".join(map(str, Study.query.all()))
    # db_session.commit()
    print "done"