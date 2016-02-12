# based on: http://alanwsmith.com/capturing-python-log-output-in-a-variable
import StringIO
import logging
log_capture_string = None

def init(name, log_level=logging.DEBUG):
    global log_capture_string
    if log_capture_string is None:
        log_capture_string = StringIO.StringIO()
    ### Create the logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    ### Link the logger to the stream
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(log_level)
    logger.addHandler(ch)
    return logger

def read():
    log_capture_string.seek(0)
    logtxt = log_capture_string.read()
    log_capture_string.truncate(0)
    return logtxt
