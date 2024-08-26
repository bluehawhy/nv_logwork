#!/usr/bin/python
# __init__.py
# -*- coding: utf-8 -*-

# import library in other folder
import os
import logging.handlers

from . import filas

from pathlib import Path
from datetime import datetime

__all__ = (
    'util_logger'
)
__version__ = '0.1.0'




def remove_message(message_path = None):
    os.remove(message_path) if Path(message_path).exists() else None
    return None

def input_message(path = None, message = None, settime=True):
    now = str(datetime.now())[0:19]
    f = open(path,'a')
    if settime == True: 
        f.write(now+' '+message+'\n')
    if settime == False:
        f.write(message+'\n')
    f.close()
    return None

def makeLogger(logfile):
    # print('start logger rootpath: '+ rootpath)
    loggerger = logging.getLogger(__name__)
    # to set log location :  filename='./log/worklogger.log'
    #loggerger.setLevel(level=logging.INFO)
    loggerger.setLevel(level=logging.DEBUG)
    file_max_bytes = 10 * 1024 * 1024

    fileHandler = logging.handlers.RotatingFileHandler(filename=logfile, maxBytes=file_max_bytes, backupCount=10)

    # formmater setting
    formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')

    # set value fileHandler and StreamHandler
    fileHandler = logging.FileHandler(filename=logfile,encoding='utf-8')
    streamHandler = logging.StreamHandler()

    # set handler and fommater
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)

    # start logging hander
    loggerger.addHandler(fileHandler)
    loggerger.addHandler(streamHandler)
    loggerger.info("start dev logging in the path : %s" %logfile)
    return loggerger

# Print header for log in Jenkins
def print_header(text: str, max_width=80):
    separator = '=' * max_width
    logging.info("\n{sep}\n{text}\n{sep}\n".format(
        sep=separator, text=text.center(max_width)))

# Print header for log in Jenkins
def print_method(method):
    def main(*args, **kwargs):
        logging.debug(f'[START] {method.__name__}')
        result = method(*args, **kwargs)
        logging.debug(f'[DONE] {method.__name__}')
        return result
    return main


log_file_name = '%s_%s.log' % (filas.executed_file_name, filas.now_date_time)
log_folder_name = os.path.join('_logs')
log_full_name = os.path.join(log_folder_name, log_file_name)
logger = makeLogger(log_full_name)