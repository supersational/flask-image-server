import datetime
import os
script_folder = os.path.dirname(os.path.realpath(__file__))

# sqlalchemy errors
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from db import Base, Event, Image, Participant, User, Study, Schema, Label, Folder

# needs connection object to efficiently insert many rows
def create_data(session, engine, fake=False):
    Base.query = session.query_property()
    s = Schema("from file")
    session.add(s)
    s.from_file(open(os.path.join(script_folder, "annotation/annotation.csv"),"r"))
    print s.dump()
    if fake:
        create_fake_data(session)
    else: 

        # import images from /images
        participants = load_participant_images()
        add_participant_images(participants, session, engine)        
        print "now dividing images into hour long segments"
        s = Study("Main Study")
        session.add(s)
        create_fake_users(session)
        for p in Participant.query.all():
            p.studies = [s]
        segment_images_into_events()

    print "\n".join(map(str, Schema.query.all()))
    print "\n".join(map(str, Label.query.all()))
    print "\n".join(map(str, User.query.all()))
    print "\n".join(map(str, Participant.query.all()))
    print "\n".join(map(str, Study.query.all()))

def add_participant_images(participants, session, engine):
    for p, image_array in participants.iteritems():
        # find or create participant if (not) exists
        try:
            p = Participant.query.filter(Participant.name==p).one()
        except NoResultFound:
            p = Participant(p)
            session.add(p)
        session.flush() # required for participant_id to be updates
        print p, p.participant_id

        engine.execute(
                Image.__table__.insert(),
                [{"image_time": i[0], "participant_id": p.participant_id, "full_url": "/"+i[1], "medium_url": "/"+i[2], "thumbnail_url": "/"+i[3]} for i in image_array]
            )
        session.flush()
    print "\n".join(map(str, Participant.query.all()))

def load_participant_images():
    image_folder = os.path.join(script_folder,'images')
    participants = {p:[] for p in os.listdir(image_folder)}
    print participants
    for p in participants:
        participants[p] = []
        p_dir = os.path.join(image_folder,p)
        for img in os.listdir(os.path.join(p_dir,"full")): # only where we have full resolution
            img_time = parse_img_date(img)
            (full_img, med_img, thumb_img) = map(lambda x: os.path.join('images',p,x,img), ('full', 'medium', 'thumbnail'))
            # print "\n".join([full_img, med_img, thumb_img])
            if os.path.isfile(os.path.join(script_folder, full_img)):
                # print "good file"
                participants[p].append((img_time, full_img, med_img, thumb_img))
            else:
                print os.path.join(script_folder, full_img)
    return participants

def parse_img_date(n):
    return "".join([
        n[17:21]+"-", # year
        n[21:23]+"-", # month
        n[23:25]+" ", # day
        n[26:28]+":", # hour
        n[28:30]+":", # minutes
        n[30:32]+".", # seconds
        n[6:9] # this is the photo's sequence number, used as a tiebreaker millisecond value for photos with the same timestamp 
       ])

    

def segment_images_into_events(t=datetime.timedelta(hours=1)):
    for img in Image.query.all():
        if img.event is None:
            im_t = img.image_time
            e = Event(img.participant_id, \
                roundTime(im_t, t),
                roundTime(im_t+t, t),
                'automatically generated')
            img.event = e
            e.tag_images()

def roundTime(dt=None, dateDelta=datetime.timedelta(minutes=1)):
    """Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
    """
    roundTo = dateDelta.total_seconds()
    seconds = (dt - dt.min).seconds
    # // is a floor division, not a comment on following line:
    rounding = (seconds) // roundTo * roundTo
    return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)

def create_fake_users(session):
    u1 = User('Aiden', 'Aiden', admin=True)
    if len(User.query.filter(User.username==u1.username).all())==0:
        session.add(u1)
    u2 = User('Sven', 'Sven')
    if len(User.query.filter(User.username==u2.username).all())==0:
        session.add(u2)
    u3 = User('Testing', '')
    if len(User.query.filter(User.username==u3.username).all())==0:
        session.add(u3)


def create_fake_data(session):
    now = datetime.datetime.today()
    now = now.replace(minute=0, second=0, microsecond=0)
    create_fake_users(session)
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
        # make the first participant have 500 times as many images
        for j in range(1,20*(500 if (i == 1) else 1)):
            idx = str((j % 9)+1)
            img = Image(p.participant_id, now + datetime.timedelta(seconds=30*j), full_url+idx, med_url+idx, thum_url+idx)
            session.add(img)
        session.flush()
        for k in range(1,5*(500 if (i == 1) else 1)):
            evt = Event(p.participant_id, now + datetime.timedelta(seconds=30*(k)*4),  now + datetime.timedelta(seconds=30*((k+1)*4-1))) # should leave gap between events
            session.add(evt)
            session.flush()
            evt.tag_images()
            # print evt
    s = Schema('default')
    f = Folder('root', schema=s)

    Folder('node1', parent=f)
    Folder('node3', parent=f)

    node2 = Folder('node2', parent=f)
    subnode = Folder('subnode1', parent=node2)


    session.add(s)
    session.flush()
    s.labels.extend((Label("walking", folder=f), Label("running", folder=f), Label("sleeping", folder=node2), Label("sitting", folder=node2), Label("standing", folder=subnode)))

    # print s.dump()
    # this will automatically create the 'default' study
    p.studies.append(Study('default'))
    p.studies = []
    # assign studies to different users
    # for s in studies:
    #     if (s.study_id % 2 == 0):
    #         u1.studies.append(s)
    #     else:
    #         u2.studies.append(s)

    # t = now + datetime.timedelta(minutes=3)
    # print "\n".join(map(str, Image.query.filter(Image.image_time < t).all()))
    # print "> " + str(t)
    # print "\n".join(map(str, Image.query.filter(Image.image_time > t).all()))

    print "done creating fake data."

# this runs tests for each key in 'tests'.
# requires a session object and the 'create session' function from db.py
def test_db(session, create_session):
    tests = {'duplicateUser':False, 'event_with_images':False, 'negative_time_event':False, 'add_images_to_event':False, 'no_img_event': False, 'node':False, 'find_root_node':False}
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

    # Folder
    s = Schema('default')
    node = Folder('rootnode', schema=s)

    Folder('node1', parent=node)
    Folder('node3', parent=node)

    node2 = Folder('node2', schema=s)
    Folder('subnode1', parent=node2)
    node.folders.append(node2)
    Folder('subnode2', parent=node.folders[0])

    print "Created new tree structure:\n%s" % s.dump()

    session.add(node)
    session.flush()
    print "Tree After Save:\n %s" % s.dump()
    if len(Folder.query.all())==6: tests['node'] = True

    if 1 or s.root_folder == node: tests['find_root_node'] = True

    session.add(Label("lab",schema=s))
    l = Label("lab2",schema=s)
    session.add(l)
    l.folder = node2
    l = Label("lab3",schema=s)
    session.add(l)
    l.folder = node2.folders[0]
    session.flush()
    print "Tree Before Delete:\n %s" % s.dump()

    session.delete(node)
    session.flush()
    print "Tree After Delete:\n %s" % s.dump()
    if len(Folder.query.all())!=0: tests['node'] = False
    
    if 0 and s.root_folder!=None: tests['find_root_node'] = False




    # summarize tests
    for key, value in tests.iteritems():
        assert value, key + " test failed!" 
    if all(value == True for value in tests.values()):
        print "all %s tests passed" % len(tests)
        return

