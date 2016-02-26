import datetime

# sqlalchemy errors
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from db import Base, Event, Image, Participant, User, Study, Schema, Label

def create_data(session):
    Base.query = session.query_property()
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
        for k in range(1,5):
            evt = Event(p.participant_id, now + datetime.timedelta(seconds=30*(k)*4),  now + datetime.timedelta(seconds=30*((k+1)*4-1))) # should leave gap between events
            session.add(evt)
            session.flush()
            evt.tag_images()
            # print evt
    s = Schema('default')
    session.add(s)
    session.flush()
    s.labels.extend((Label("walking"), Label("running"), Label("sleeping"), Label("sitting"), Label("standing")))
    print "\n".join(map(str, Schema.query.all()))
    print "\n".join(map(str, Label.query.all()))
    
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

def test_db(session, create_session):
    tests = {'duplicateUser':False, 'event_with_images':False, 'negative_time_event':False, 'add_images_to_event':False, 'no_img_event': False}
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
