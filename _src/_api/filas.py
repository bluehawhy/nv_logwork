#!/usr/bin/python
# filepath.py
# -*- coding: utf-8 -*-

'''
Created on 2018. 11. 15.
release note
2022-11-25 : set release note.

@author: miskang

'''

import os
import sys
import platform
import datetime
import pathlib

operation = platform.system()
now = datetime.datetime.now()
nowdate = str(now.strftime('%Y-%m-%d')).replace('-', '')
nowtime = str(now.strftime('%H:%M:%S')).replace(':', '')
sep = ""

if operation == "Windows":
    sep = '\\'

elif operation == "Linux":
    sep = r'/'

# currntfile = mainpath.split(sep)[-1]
now_date_time = '%s_%s' % (nowdate, nowtime)


executed_file_name = sys.argv[0].split('/')[-1].split('\\')[-1].replace('.py','').replace('.exe','')
main_path = os.path.dirname(sys.argv[0])

filepath_abspath = os.path.dirname(os.path.abspath(__file__))
filepath_realpath = os.path.dirname(os.path.realpath(__file__))

#print('filepath_abspath: %s' %filepath_abspath)
#print('filepath_realpath: %s' %filepath_realpath)
#print('main_path: %s' %main_path)
#print('executed_file_name: %s' %executed_file_name)