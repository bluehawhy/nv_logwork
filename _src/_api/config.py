#!/usr/bin/python
#config.py
# -*- coding: utf-8 -*-

'''
Created on 2018. 11. 15.

@author: miskang

'''
import os
import json
logwork_config_default = {
	"last_file_path": "",
	"task_type": {
		"project": "{\"input_playload\":{\"fields\":{\"project\": {\"key\": \"field_input_value\"}}}}",
		"issuetype": "{\"input_playload\":{\"fields\": { \"issuetype\": {\"name\": \"field_input_value\"}}}}",
		"summary": "{\"input_playload\":{\"fields\":{\"summary\":\"field_input_value\"}}}",
		"assignee": "{\"input_playload\":{\"fields\":{\"assignee\":{\"name\":\"field_input_value\"}}}}",
		"priority": "{\"input_playload\":{\"fields\":{\"priority\":{\"name\":\"field_input_value\"}}}}",
		"description": "{\"input_playload\":{\"fields\":{\"description\":\"field_input_value\"}}}",
		"taskcategory": "{\"input_playload\":{\"fields\":{\"customfield_10643\":{\"value\":\"field_input_value\"}}}}",
		"tqa_1_cate": "{\"input_playload\":{\"fields\":{\"customfield_15501\":{\"value\":\"field_input_value\"}}}}",
		"tqa_2_cate": "{\"input_playload\":{\"fields\":{\"customfield_15502\":{\"value\":\"field_input_value\"}}}}",
		"tqa_3_cate": "{\"input_playload\":{\"fields\":{\"customfield_15503\":{\"value\":\"field_input_value\"}}}}",
		"tqa_task": "{\"input_playload\":{\"fields\":{\"customfield_15504\":{\"value\":\"field_input_value\"}}}}",
		"version": "{\"input_playload\":{\"fields\":{\"customfield_10229\":\"field_input_value\"}}}",
		"tqa_project": "{\"input_playload\":{\"fields\":{\"customfield_15511\":{\"value\":\"field_input_value\"}}}}",
		"originalestimate": "{\"input_playload\":{\"fields\":{\"timetracking\":{\"originalEstimate\":\"field_input_value\"}}}}",
		"duedate": "{\"input_playload\":{\"fields\":{\"duedate\":\"field_input_value\"}}}",
		"plannedstart": "{\"input_playload\":{\"fields\":{\"customfield_10103\":\"field_input_value\"}}}",
		"plannedend": "{\"input_playload\":{\"fields\":{\"customfield_10104\":\"field_input_value\"}}}",
		"tqa_variant": "{\"input_playload\":{\"fields\":{\"customfield_15510\":{\"value\":\"field_input_value\"}}}}"	
	},
	"logwork_type":{
		"key" : "{\"key\": \"field_input_value\"}",
		"summary" : "{\"summary\": \"field_input_value\"}",
		"description" : "{\"input_playload\":{\"comment\": \"field_input_value\"}}",
		"logwork_start" : "{\"input_playload\":{\"started\": \"field_input_value\"}}",
		"spent_second" : "{\"input_playload\":{\"timeSpentSeconds\": \"field_input_value\"}}",
		"user" : "{\"input_playload\":{\"author\": {\"name\": \"field_input_value\"}}}"
	}
}
def load_config(filename):
    config_value={}
    if not os.path.isfile(filename):
        #make json file if not exist
        with open(filename, 'w', encoding='utf-8') as jsonFile:
            #get default value from list
            if 'logwork' in filename:
                json.dump(logwork_config_default, jsonFile, ensure_ascii=False, indent ='\t')
    with open(filename, 'r', encoding='utf-8') as data_file:
        config_value = json.load(data_file)
    return config_value

def save_config(json_dict,filename):
    with open(filename, 'w', encoding='utf-8') as jsonFile:
        json.dump(json_dict, jsonFile,ensure_ascii=False, indent ='\t')
    return None
