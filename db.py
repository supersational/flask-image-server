# coding: utf-8
# from:
# C:\Users\shollowell\Documents\wearable-webapp\python-flask>sqlacodegen postgres://postgres:testing@localhost:3145/linker
import datetime
# define database
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint, text
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

    participant = relationship(u'Participant', back_populates='events')
    images = relationship(u'Image', back_populates='event', order_by='Image.image_time')

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

    def prev_event(self):
        prev_events = Event.query.filter((Event.participant_id==self.participant_id) & (Event.end_time < self.end_time)).all()
        if len(prev_events)==0:
            return None
        return max(prev_events, key=lambda x: x.end_time)

    def next_event(self):
        next_events = Event.query.filter((Event.participant_id==self.participant_id) & (Event.start_time > self.start_time)).all()
        if len(next_events)==0:
            return None
        return min(next_events, key=lambda x: x.end_time)
    
    def prev_image(self):
        imgs = Image.query.filter(
            (Image.participant_id==self.participant_id) &
            (Image.image_time<self.end_time) &
            ((Image.event_id!=self.event_id) | (Image.event_id==None))
            ).all()
        if len(imgs)>0:
            return max(imgs, key=lambda x: x.image_time)
        return None

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
        with self.next_event() as next:
            if next.start_time < self.end_time:
                mid = self.end_time + (next.start_time - self.end_time)/2
                next.start_time = mid
                self.end_time = mid - datetime.timedelta.resolution
        with self.prev_event() as prev:
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
        return self.image_id == self.event.first_image.image_id

    @hybrid_property 
    def is_last(self):
        return self.image_id == self.event.last_image.image_id

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
    images = relationship(u'Image', back_populates='participant')
    events = relationship(u'Event', back_populates='participant')
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        txt = 'Participant: %s (id=%s, %s images, ' % (self.name, self.participant_id, len(self.images))
        if len(self.studies)>5:
            return txt + ' in %s studies)' % len(self.studies)
        else:
            return txt + ' studies=%s)' % [x.name for x in self.studies]
    
    def get_images_by_hour(self):
        # cur.execute("""SELECT image_time FROM Images WHERE Images.participant_id=%s""", [participant_id])
        data =  [x.image_time for x in self.images]
        # for x in data:
        #   print x
        # data_by_day = map(lambda x: x[0].toordinal(), data)
        unique_days = {}
        for time in data:
            day = str(datetime.date(time.year,time.month,time.day))
            hour = time.hour
            print day
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
        return unique_days

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
    password = Column(String(50))
    # UniqueConstraint('username')
    studies = relationship(u'Study', secondary='useraccess', back_populates='users')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
            return 'User: %s (id=%s, password=%s, %s studies)' % (self.username, self.user_id, '*' * len(self.password), len(self.studies))

def drop_db():
    Base.metadata.drop_all(engine)

def create_session(autoflush=True, autocommit=True):
    return scoped_session(sessionmaker(autocommit=autocommit,
                                             autoflush=autoflush,
                                             bind=engine))  
def create_db(drop=False):
    global session
    session = create_session()
    Base.metadata.create_all(engine)
    return session

def get_session(create_data=False, run_tests=False):

    if run_tests:
        # running tests requires an empty database
        drop_db()
        # will throw error if test fails
        test_db()
        drop_db()

    # does not actually connect until work is done
    session = create_db()
    Base.query = session.query_property()
        
    if create_data:
        now = datetime.datetime.today()
        now = now.replace(minute=0, second=0, microsecond=0)
        u1 = User('Aiden', 'Aiden')
        if len(User.query.filter(User.username==u1.username).all())==0:
            session.add(u1)
        u2 = User('Sven', 'Sven')
        if len(User.query.filter(User.username==u2.username).all())==0:
            session.add(u2)
        u3 = User('Testing', '')
        if len(User.query.filter(User.username==u3.username).all())==0:
            session.add(u3)
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
                idx = str((j % 9)+1)
                img = Image(p.participant_id, now + datetime.timedelta(seconds=30*j), full_url+idx, med_url+idx, thum_url+idx)
                session.add(img)
            session.flush()
            read_log()
            for k in range(1,5):
                evt = Event(p.participant_id, now + datetime.timedelta(seconds=30*(k)*4),  now + datetime.timedelta(seconds=30*((k+1)*4-1))) # should leave gap between events
                session.add(evt)
                session.flush()
                evt.tag_images()
                # print evt

        # this will automatically create the 'default' study
        p.studies.append(Study('default'))
        p.studies = []
        # assign studies to different users
        for s in studies:
            if (s.study_id % 2 == 0):
                u1.studies.append(s)
            else:
                u2.studies.append(s)
        print "\n".join(map(str, User.query.all()))
        print "\n".join(map(str, Participant.query.all()))
        print "\n".join(map(str, Study.query.all()))
        # t = now + datetime.timedelta(minutes=3)
        # print "\n".join(map(str, Image.query.filter(Image.image_time < t).all()))
        # print "> " + str(t)
        # print "\n".join(map(str, Image.query.filter(Image.image_time > t).all()))

        print "done creating fake data."
        # print loghandler.read()
    return session

def test_db():
    tests = {'duplicateUser':False, 'event_with_images':False, 'negative_time_event':False, 'add_images_to_event':False, 'no_img_event': False}
    session = create_db()
    Base.query = session.query_property()
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


    # delete event with no images
    p = Participant("test")
    session.add(p)
    session.flush() # get p.id
    evt = Event(p.participant_id, datetime.datetime.today(), datetime.datetime.today() + datetime.timedelta(minutes=1))
    session.add(evt)
    print "evts : " + str(session.query(Event).all())
    evt.check_valid()
    evts = session.query(Event).all()
    # print "evts : " + str(evts)
    if len(evts)==0:
        print "db deleted event with no images, good!"
        tests['no_img_event'] = True
    else:
        print "db didn't delete event with no images!!"

    now = datetime.datetime.today()
    # create 2 images just inside the event boundary, and 2 just outside 
    img_start = Image(p.participant_id, now, "","","")
    session.add(img_start) # should be added to event
    img_end = Image(p.participant_id, now+datetime.timedelta(minutes=1), "","","")
    session.add(img_end) # should be added to event
    img_before = Image(p.participant_id, now-datetime.timedelta.resolution, "","","")
    session.add(img_before) # should not be added to event
    img_after = Image(p.participant_id, now+datetime.timedelta(minutes=1)+datetime.timedelta.resolution, "","","")
    session.add(img_after) # should not be added to event
    evt = Event(p.participant_id, now, now + datetime.timedelta(minutes=1))
    session.add(evt)
    session.flush()
    evt.tag_images()
    if len(filter(lambda x: x.image_id == img_start.image_id or x.image_id == img_end.image_id, evt.images))==2 and len(evt.images)==2:
        print "db added the correct 2 images out of 4 to the event, good!"
        tests['add_images_to_event'] = True
    else:
        print "db didn't assign correct images to event!!"#
        print 'evt.images' + str(evt.images)
        print 'should contain: ' + str([img_start, img_end])
    evt.check_valid()
    # make sure we don't delete this valid event
    evts = session.query(Event).all()
    if len(evts)==1:
        print "db didn't delete a valid event, good!"
        tests['event_with_images'] = True
    else:
        print "db deleted a valid event!!"
        print "evts %s: " % len(evts) + str(evts)

    # evts = session.query(Event).all()
    # print "evts %s: " % len(evts) + str(evts)
    # test deleting of event due to start_time < end_time
    print "min time resolution : " + str(datetime.timedelta.resolution) 
    evt.end_time = evt.start_time - datetime.timedelta.resolution*2
    evt.check_valid()
    evts = session.query(Event).all()
    if len(evts)==0:
        print "db deleted an event that had 'negative' duration, good!"
        tests['negative_time_event'] = True
    else:
        print "db didn't delete an event with invalid start/end times!!"
        print "evts %s: " % len(evts) + str(evts)

    # summarize tests
    for key, value in tests.iteritems():
        assert value, key + " test failed!" 
    if all(value == True for value in tests.values()):
        print "all %s tests passed" % len(tests)
        return

if __name__ == "__main__":
    drop_db()
    get_session(create_data=True, run_tests=True)
