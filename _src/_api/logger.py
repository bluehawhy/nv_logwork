#!/usr/bin/python
# __init__.py
# -*- coding: utf-8 -*-

# import library in other folder
import os
import logging.handlers

from . import filepath

__all__ = (
    'util_logger'
)
__version__ = '0.1.0'


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
    fileHandler = logging.FileHandler(filename=logfile)
    streamHandler = logging.StreamHandler()

    # set handler and fommater
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)

    # start logging hander
    loggerger.addHandler(fileHandler)
    loggerger.addHandler(streamHandler)
    loggerger.info("start dev logging in the path : %s" %logfile)
    return loggerger


log_file_name = '%s_%s.log' % (filepath.executed_file_name, filepath.now_date_time)
log_folder_name = os.path.join('_logs')
log_full_name = os.path.join(log_folder_name, log_file_name)
print(log_full_name)
logger = makeLogger(log_full_name)