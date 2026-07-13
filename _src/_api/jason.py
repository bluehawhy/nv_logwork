# -*- coding: utf-8 -*-
#!/usr/bin/python
#WorklogBulk.py

import os
import sys
import json

from . import configus

def makeplayload(dic):
    data = json.dumps(dic,ensure_ascii=False).encode('utf8')
    return data

def make_json(str):
    data = json.loads(str)
    return data

def make_playload(dict_data,dict_config):
    temp_payloads = {}
    temp_json =''
    ignore_list = ['None','0']
    for data_key in dict_data.keys():
        if dict_data[data_key] not in ignore_list:
            if data_key in dict_config.keys() :
                str_playload = str(dict_config[data_key]).replace('field_input_value',dict_data[data_key]).replace('\n','\\r\\n')
                temp_json = json.loads(str_playload)
                merge_playload(temp_payloads,temp_json)
    return temp_payloads

def merge_playload(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_playload(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a
