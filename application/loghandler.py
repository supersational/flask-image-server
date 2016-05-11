# based on: http://alanwsmith.com/capturing-python-log-output-in-a-variable
import StringIO
import logging
import time
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine

log_capture_string = None
logger = None
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    logger.info("Start Query: %s", statement)

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    logger.info("Query Complete!")
    logger.info("Total Time: %f", total)


def init(name, log_level=logging.DEBUG):
    global log_capture_string, logger
    if log_capture_string is None:
        log_capture_string = StringIO.StringIO()
    ### Create the logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    ### Link the logger to the stream
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(log_level)
    logger.addHandler(ch)
    ### Add a log-file for good measure
    logger.addHandler(logging.FileHandler('logs/logfile'+datetime.now().strftime('%Y-%m-%d-%H-%M')+'.txt'))
    ### For disabling HTTP stdout messages from flask
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    return logger

def read():
    log_capture_string.seek(0)
    logtxt = log_capture_string.read()
    log_capture_string.truncate(0)
    return logtxt

