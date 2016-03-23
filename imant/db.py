# coding: utf-8
# https://www.python.org/dev/peps/pep-0249/
from config import NODE_SECRET_KEY, SQLALCHEMY_DATABASE_URI
import datetime, sys
from collections import OrderedDict
# security
import hashlib, uuid
# define database
from sqlalchemy import Column, Date, DateTime, Boolean, ForeignKey, Integer, String, Table, Text, UniqueConstraint, text
from sqlalchemy.sql.expression import func, funcfilter
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
# sqlalchemy errors
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
# create session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
# to support Folder:
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection
# for generating commands for executing raw SQL
from sqlalchemy.sql import text
# jsonifying objects
from json import dumps as json_dumps
# custom data creation class


Base = declarative_base()
metadata = Base.metadata

engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True, logging_name="sqlalchemy.engine")
connection = engine.connect()

# logging
import loghandler, time

logger = loghandler.init("sqlalchemy.engine")

def read_log():
    return loghandler.read()

class Event(Base):
    __tablename__ = 'events'

    event_id = Column(Integer, primary_key=True)
    participant_id = Column(ForeignKey(u'participants.participant_id'), nullable=False)
    label_id = Column(ForeignKey(u'labels.label_id'))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    comment = Column(Text)
    number_times_viewed = Column(Integer)

    participant = relationship(u'Participant', back_populates='events')
    images = relationship(u'Image', back_populates='event', order_by='Image.image_time')
    label = relationship(u'Label', back_populates='events')

    def __init__(self, participant_id, start_time, end_time, comment=''):
        self.participant_id = participant_id
        self.start_time = start_time
        self.end_time = end_time
        self.comment = comment
        self.number_times_viewed = 0

    def get_images(self):
        return Image.query.filter((Image.participant_id==self.participant_id) & (self.contains(Image))).order_by(Image.image_time.desc()).all()

    def tag_images(self):
        for image in self.get_images():
            image.event_id = self.event_id

    def check_valid(self):
        if self.length < datetime.timedelta(0):
            print "event start_time > end_time. deleting.."
            self.delete()
            return False
        if len(self.images)==0:
            print "no images in event. deleting.."
            self.delete()
            return False
        return True
        Event.query.filter(Event.prev_event==some_event).one()
    @hybrid_property 
    def prev_event(self):
        prev_events = Event.query.filter((Event.participant_id==self.participant_id) & (Event.end_time < self.end_time)).all()
        if len(prev_events)==0:
            return None
        return max(prev_events, key=lambda x: x.end_time)

    @hybrid_property 
    def next_event(self):
        next_events = Event.query.filter((Event.participant_id==self.participant_id) & (Event.start_time > self.start_time)).all()
        if len(next_events)==0:
            return None
        return min(next_events, key=lambda x: x.end_time)

    @hybrid_property 
    def prev_image(self):
        imgs = Image.query.filter(
            (Image.participant_id==self.participant_id) &
            (Image.image_time<self.end_time) &
            ((Image.event_id!=self.event_id) | (Image.event_id==None))
            ).all()
        if len(imgs)>0:
            return max(imgs, key=lambda x: x.image_time)
        return None

    @hybrid_property 
    def next_image(self):
        imgs = Image.query.filter(
            (Image.participant_id==self.participant_id) &
            (Image.image_time>self.start_time) &
            ((Image.event_id!=self.event_id) | (Image.event_id==None))
            ).all()
        if len(imgs)>0:
            return min(imgs, key=lambda x: x.image_time)
        return None

    def add_image(self, image):
        print self.images
        if type(image) is int:
            print "assume " + str(image) + " is an image ID"
            return add_image(images.query.filter(Image.image_id==image).one())

        if image.event_id == self.event_id:
            print "image to be added is already in the event"
            raise ValueError("image to be added is already in the event")
        affected_events = [self] # events that will need times modified and might need deleting
        if image.event: affected_events.append(image.event)
        image.event_id = self.event_id
        if image.image_time > self.end_time:
            # image after end of event
            images_between = Image.query.filter((Image.participant_id==self.participant_id) & (Image.image_time > self.end_time) & (Image.image_time < image.image_time)).all()
            self.end_time = image.image_time
        elif image.image_time < self.start_time:
            # image before start of event
            images_between = Image.query.filter((Image.participant_id==self.participant_id) & (Image.image_time < self.start_time) & (Image.image_time > image.image_time)).all()
            self.start_time = image.image_time
        else:
            print "image must already be within event boundary! (wierd)"
            raise ValueError("image must already be within event boundary! (wierd)")
        print "my images:", len(self.images)
        print "images between: ", len(images_between)
        for img in images_between:
            print img
            affected_events.append(img.event)
            img.event_id = self.event_id

        print "I now have %d images, and %d affected_events (%d total)" % (len(self.images), len(set(affected_events)), len(affected_events))
        for evt in set(affected_events):
            print evt.event_id, " - ", len(evt.images)
            if evt.adjust_time(): 
                print "still valid"
        print self.images
        return True

    def remove_left(self, image, steal=True, include_target=True):
        print 'incllude_target', include_target
        if image.event_id!=self.event_id:
            raise ValueError("image to be removed isn't in event")
        if steal and self.prev_event is not None:
            prev = self.prev_event
            for img in [x for x in self.images if x.image_time <= image.image_time]:
                if include_target or img.image_id!=image.image_id: 
                    img.event_id = prev.event_id
                    print img.image_id, "added to event ", prev.event_id 
        else: 
            # set to no event
            for img in [x for x in self.images if x.image_time <= image.image_time]:
                if include_target or img.image_id!=image.image_id: 
                    img.event_id = None
                    print img.image_id, "removed" , image.image_id , image.image_id!=img.image_id
        return True

    def remove_right(self, image, steal=True, include_target=True):
        if image.event_id!=self.event_id:
            raise ValueError("image to be removed isn't in event")
        if steal and self.next_event is not None:
            next = self.next_event
            for img in [x for x in self.images if x.image_time >= image.image_time]:
                if include_target or img.image_id!=image.image_id: 
                    img.event_id = next.event_id
                    print img.image_id, " added to event ", next.event_id
        else: 
            # set to no event
            for img in [x for x in self.images if x.image_time >= image.image_time]:
                if include_target or img.image_id!=image.image_id: 
                    img.event_id = None
                    print img.image_id, " removed" 
        return True

    def split_left(self, image):
        index = self.images.index(image)
        if not index is None and index>0:
            new_event = Event(self.participant_id, self.start_time, self.end_time, self.comment)
            for img in self.images[:index]:
                img.event = new_event
            new_event.adjust_time()
            self.adjust_time()
            return True
        return False

    def split_right(self, image):
        index = self.images.index(image)+1
        if not index is None and index<len(self.images):
            new_event = Event(self.participant_id, self.start_time, self.end_time, self.comment)
            for img in self.images[index:]:
                img.event = new_event
            new_event.adjust_time()
            self.adjust_time()
            return True
        return False

    def delete(self):
        for img in Image.query.filter(Image.event_id==self.event_id).all():
            img.event_id = None 
        Event.query.filter(Event.event_id==self.event_id).delete()
        print "deleted"

    def adjust_time(self):
        start_time = datetime.datetime.max
        end_time = datetime.datetime.min
        for image in self.images:
            start_time = min(start_time, image.image_time)
            end_time = max(end_time, image.image_time)

        if start_time < end_time:
            print "adjusting time %s - %s " % (start_time, end_time)
            self.start_time = start_time
            self.end_time = end_time
            self.tag_images()
            return True
        else:
            return self.check_valid()

    def resolve_time_conflicts(self):
        with self.next_event as next:
            if next.start_time < self.end_time:
                mid = self.end_time + (next.start_time - self.end_time)/2
                next.start_time = mid
                self.end_time = mid - datetime.timedelta.resolution
        with self.prev_event as prev:
            if prev.end_time > self.start_time:
                mid = self.start_time + (prev.end_time - self.start_time)/2
                prev.end_time = mid
                self.start = mid + datetime.timedelta.resolution
                
    @hybrid_property 
    def length(self):
        return self.end_time - self.start_time

    @hybrid_property 
    def first_image(self):
        if len(self.images) > 0:
            return self.images[0]
        return None

    @hybrid_property 
    def last_image(self):
        if len(self.images) > 0:
            return self.images[-1]
        return None

    @hybrid_method
    def contains(self, image):
        return (self.start_time <= image.image_time) & (image.image_time <= self.end_time)

    def __repr__(self):
        return "Event: %s, %s - %s, participant_id:%s, %s images.\n%s" % (self.event_id, self.start_time, self.end_time, self.participant_id, len(self.images), "\n".join([str(i.image_time)+i.full_url for i in self.images]))

    def to_array(self):
        return [self.event_id,
                self.label_id,
                self.comment,
                map(serialize_datetime, [self.start_time, self.end_time])]

def serialize_datetime(d):
    return [d.year, d.month, d.day, d.hour, d.minute, d.second]

class Image(Base):
    __tablename__ = 'images'

    image_id = Column(Integer, primary_key=True)
    image_time = Column(DateTime, nullable=False)
    participant_id = Column(ForeignKey(u'participants.participant_id'), nullable=False)
    event_id = Column(ForeignKey(u'events.event_id'))
    full_url = Column(String(256))
    medium_url = Column(String(256))
    thumbnail_url = Column(String(256))

    event = relationship(u'Event', back_populates='images')
    participant = relationship(u'Participant', back_populates='images')

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

    @hybrid_property 
    def is_first(self):
        return self.image_id == self.event.first_image.image_id if self.event is not None else False

    @hybrid_property 
    def is_last(self):
        return self.image_id == self.event.last_image.image_id if self.event is not None else False

    def to_array(self):
        return [self.image_id, 
            self.event_id,
            self.participant_id,
            serialize_datetime(self.image_time), 
            map(self.gen_url, [self.thumbnail_url, self.medium_url, self.full_url]),
            [1 if self.is_first else 0, 1 if self.is_last else 0]
        ]

    @hybrid_method
    def gen_url(self, url): 
        url = url.replace('\\','/')
        t = int(time.time())
        return 'http://127.0.0.1:5001'+url+"?t="+str(t)+"&k="+gen_hash(t, url)

def gen_hash(t, url):
    s = str(t)+url+NODE_SECRET_KEY
    # print s
    sha512_hash = hashlib.sha512()
    sha512_hash.update(s)
    return sha512_hash.hexdigest()

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

    studies = relationship(u'Study', secondary='studyparticipants', back_populates='participants')
    images = relationship(u'Image', back_populates='participant', lazy='dynamic')
    events = relationship(u'Event', back_populates='participant')
    def __init__(self, name):
        self.name = name


    def __repr__(self):
        txt = 'Participant: %s (id=%s, %s images, ' % (self.name, self.participant_id, len(self.images.all()))
        if len(self.studies)>5:
            return txt + ' in %s studies)' % len(self.studies)
        else:
            return txt + ' studies=%s)' % [x.name for x in self.studies]
    
    @hybrid_method
    def get_images(self):
        return Image.query.filter(Image.participant_id==self.participant_id)
    @hybrid_property
    def num_images(self):
        return connection.execute(text("SELECT COUNT(*) FROM images WHERE (participant_id=:pid)"), {"pid":self.participant_id}).first()[0];

    def get_images_by_hour(self):
        unique_days = {}
        for time in connection.execute(text("SELECT DISTINCT DATE_TRUNC('HOUR', image_time) FROM images WHERE (participant_id=:pid)"), {"pid":self.participant_id}):
            # print time[0]
            # print type(time[0])
            # print time[0].day, time[0].hour
            day = time[0].strftime("%Y-%m-%d")
            hour = time[0].hour
            if day in unique_days:
                if hour in unique_days[day]:
                    unique_days[day][hour] += 1
                else: unique_days[day][hour] = 1
            else: 
                unique_days[day] = {}
                unique_days[day][hour] = 1
        # for day in unique_days:
        #   print day
        #   for hour in unique_days[day]:
        #       print day, "- " + str(hour) + ":00 : ", unique_days[day][hour], " images"
        return OrderedDict(sorted(unique_days.items(), key=lambda  d:d[0]))


t_useraccess = Table(
    'useraccess', metadata,
    Column('user_id', Integer, ForeignKey(u'users.user_id')),
    Column('study_id', Integer, ForeignKey(u'studies.study_id')),
    Column('access_level', Integer, nullable=False, default=2)
)

class Study(Base):
    __tablename__ = 'studies'

    study_id = Column(Integer, primary_key=True)
    name = Column(String(256))
    participants = relationship(u'Participant', secondary='studyparticipants', back_populates='studies')
    users = relationship(u'User', secondary='useraccess', back_populates='studies')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
            return 'Study: %s (id=%s, participants=%s)' % (self.name, self.study_id, [x.name for x in self.participants])
    


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(128))
    salt = Column(String(32))
    admin = Column(Boolean, default=False)

    studies = relationship(u'Study', secondary='useraccess', back_populates='users')

    def __init__(self, username, password, admin=False):
        self.username = username
        self.salt = uuid.uuid4().hex
        set_password(password)
        self.admin = admin
        
    # authentication methods    
    def is_authenticated(self):
        print "is_authenticated"
        return True
 
    def is_active(self):
        print "is_active"
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        print "get_id"
        return unicode(self.user_id)

    def set_password(self, new_password):
        self.password = hashlib.sha512(new_password + self.salt).hexdigest()

    def check_password(self, password):
        return self.password == hashlib.sha512(password + self.salt).hexdigest()

 
    def __repr__(self):
        return 'User: %s (id=%s, password=%s, %s studies)' % (self.username, self.user_id, '*' * len(self.password), len(self.studies))


class Schema(Base):
    __tablename__ = 'schemas'

    schema_id = Column(Integer, primary_key=True)
    name = Column(String(50))

    labels = relationship(u'Label', back_populates='schema')
    folders = relationship(u'Folder', back_populates='schema')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Schema: %s, (id=%s, %s labels)" % (self.name, self.schema_id, len(self.labels))

    @hybrid_property
    def root_folders(self):
        return [f for f in self.folders if f.parent is None]
        
    def dump(self, _indent=0):
        return "   " * _indent + repr(self) + \
                    "\n" + \
                    "".join([
                        c.dump(_indent + 1)
                        for c in [f for f in self.folders if f.parent is None]]
                    )

    def from_file(self, annotation_file):
        for line in annotation_file:
            if len(line)<=1: continue
            names = line.split(";")
            curr_folder = self
            for i, n in enumerate(names):
                if i==len(names)-1:
                    curr_folder.labels.append(Label(n, schema=self, folder=curr_folder))
                else:
                    try:
                        subfolder = filter(lambda x: x.name==n, curr_folder.folders)[0]
                    except IndexError:
                        subfolder = Folder(n, schema=self, parent=curr_folder if self!=curr_folder else None)
                        curr_folder.folders.append(subfolder)                
                         # = next(x for x in curr_folder.folders if lambda x: x.name==n)
                    # print i, subfolder
                    curr_folder = subfolder
        return self
                
class Label(Base):
    __tablename__ = 'labels'

    label_id = Column(Integer, primary_key=True)
    schema_id = Column(ForeignKey(u'schemas.schema_id'), nullable=False)
    folder_id = Column(ForeignKey(u'folders.id'))
    name = Column(String(256))
    color = Column(String(50))
    UniqueConstraint('name', 'schema_id') # schemas contain uniquely named labels

    schema = relationship(u'Schema', back_populates='labels')
    folder = relationship(u'Folder', back_populates='labels') # can belong to folder
    events = relationship(u'Event', back_populates='label')

    def __init__(self, name, schema=None, folder=None):
        self.name = str(name).rstrip()
        if isinstance(schema, Schema):
            self.schema = schema
        if isinstance(folder, Folder):
            self.folder = folder

    def __repr__(self):
        return "Label: %s, (id=%s)" % (self.name, self.label_id)
 

class Folder(Base):
    # http://docs.sqlalchemy.org/en/latest/_modules/examples/adjacency_list/adjacency_list.html

    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey(id))
    name = Column(String(255), nullable=False)
    schema_id = Column(ForeignKey(u'schemas.schema_id'), nullable=False)

    folders = relationship("Folder",
        # cascade deletions
        cascade="all, delete-orphan",
        # many to one + adjacency list - remote_side
        # is required to reference the 'remote'
        # column in the join condition.
        backref=backref("parent", remote_side=id),

        # children will be represented as a dictionary
        # on the "name" attribute.
        # collection_class=attribute_mapped_collection('name'),
    )
    labels = relationship(u"Label", back_populates='folder',cascade="all")
    schema = relationship(u'Schema', back_populates='folders')

    def __init__(self, name, parent=None, schema=None):
        self.name = name
        self.parent = parent
        if not parent is None:
            self.schema = parent.schema
        elif isinstance(schema, Schema):
            self.schema = schema

    def __repr__(self):
        return "Folder(name=%r, id=%r, parent_id=%r, labels=%s)" % (self.name, self.id, self.parent_id, \
            ",".join(map(lambda l: str(l.name).rstrip()[:20], self.labels)))



    def dump(self, _indent=0):
        return "   " * _indent + repr(self) + \
                    "\n" + \
                    "".join([
                        c.dump(_indent + 1)
                        for c in self.folders]
                    )

def drop_db():
    Base.metadata.drop_all(engine)

def create_db():
    Base.metadata.create_all(engine)

def create_session(autoflush=True, autocommit=True):
    return scoped_session(sessionmaker(autocommit=autocommit,
                                             autoflush=autoflush,
                                             bind=engine))  

def get_session(create_data=False, run_tests=False):
    if run_tests:
        # running tests requires an empty database
        drop_db()
        # will throw error if test fails
        create_db()
        db_data.test_db(session, create_session)
        drop_db()

    # does not actually connect until work is done
    print "creating db"
    create_db()
    session = create_session()
    Base.query = session.query_property()
    if create_data:
        if "--real" in sys.argv:
            db_data.create_data(session, engine, fake=False)
        else:
            db_data.create_data(session, engine, fake=True)
    return session

import db_data
if __name__ == "__main__":
    drop_db()
    global session
    session = get_session(create_data=True, run_tests=True)
# else:
#     session = get_session()