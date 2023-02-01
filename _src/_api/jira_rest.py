# rest.py
# !/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2018. 11. 15.
@author: miskang
'''

# This script shows how to connect to a JIRA instance with a
# username and password over HTTP BASIC authentication.
import os
import sys
# import requests library for making REST calls
import json
import requests

from . import logger
from . import playload
from . import config

config_path = os.path.join('static','config','config.json')
config_data =config.load_config(config_path)
jira_url = config_data['jira_url']
logging = logger.logger
# =============================================================================================

headers = {
    'Cache-Control': 'no-cache',
    # 'Accept': 'application/json;charset=UTF-8',  # default for REST
    # 'Accept': 'application/json',  # default for REST
    # 'Pragma': 'no-cache',
    # 'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'
    'Content-Type': 'application/json',  # ;charset=UTF-8',
    'X-Atlassian-Token': 'no-check'}


def initsession(username, password):
    logging.info("start log in from rest.py")
    # Create Session
    logging.debug("make session")
    s = requests.Session()
    login_url = jira_url+'/rest/auth/1/session'
    payload = {"username": username, "password": password}
    session = None
    session_info = None
    try:
        logging.debug("try log in")
        session_info = s.post(login_url, data=json.dumps(payload), headers=headers, timeout=30)
    except Exception as e:    # This is the correct syntax
        logging.info("Fail to log in Reason: %s" % str(e))
        session_info = None
    else:
        if session_info.status_code == 200:
            logging.info("log in success!")
        else:
            logging.info("Fail to log in Reason: %s" % str(session_info.text))
            logging.debug(session_info)
            session_info = None
    session = s
    return session,session_info


class Handler_Jira():
    '''docstring for Handler_Jira'''

    def __init__(self, session):
        self.session = session

    def searchIssueCountByQuery(self, query):
        self.all_issues = {}
        self.issue = {}
        self.url = jira_url+'/rest/api/2/search?startAt=0&maxResults=1&jql=%s' % query
        self.response = self.session.get(self.url, timeout=100.0).json()
        self.issuecount = self.response['total']
        return self.issuecount

    def searchIssueByQuery(self, query):
        self.all_issues = {}
        self.issue = {}
        self.url = jira_url+'/rest/api/2/search?startAt=0&maxResults=1&jql=%s' % query
        self.response = self.session.get(self.url, timeout=100.0).json()
        self.issuecount = self.response['total']
        logging.debug('issue count: %s' % self.issuecount)
        self.start = 0
        self.maxResults = 1000
        while self.start <= self.issuecount:  # Spaces around !=. Makes Guido van Rossum happy.
            self.url = jira_url+'/rest/api/2/search?startAt=%s&maxResults=%s&jql=%s' % (
            self.start, self.maxResults, query)
            logging.debug(self.url)
            self.response = self.session.get(self.url, timeout=100.0).json()
            for self.re in self.response['issues']:
                # print(self.re)
                self.issue = {str(self.re['key']): self.re['fields']}
                self.all_issues.update(self.issue)
            self.start += 1000
        self.issues = self.all_issues
        return self.issues

    def searchIssueByKey(self, key):
        self.key = key
        self.url = jira_url+'/rest/api/2/issue/%s' % self.key
        self.response = self.session.get(self.url, timeout=10.0).json()
        return self.response

    def createTicket(self, payloads):
        # ============= init =====================
        self.url = jira_url+'/rest/api/2/issue'
        self.payload = payloads
        #logging.debug(self.payload)
        self.response = self.session.post(self.url, data=playload.makeplayload(self.payload), headers=headers,
                                          timeout=10.0)
        #self.code = self.response.status_code
        #self.info = json.loads(self.response.text)
        #logging.debug('code :%s' % self.code)
        #logging.debug('info :%s' % self.info)
        return self.response

    def updateissue(self, key, payloads):
        # update issue
        self.key = key
        self.url = jira_url+'/rest/api/2/issue/%s' % self.key
        self.payload = payloads
        self.headers = headers
        # logging.debug("update url: %s" %self.url)
        self.response = self.session.put(self.url, data=playload.makeplayload(self.payload), headers=headers,
                                         timeout=10.0)
        #logging.debug(self.response.text)
        logging.debug("Done: %s and code: %s" % (self.key, self.response.status_code))
        return self.response

    def createLinked(self, key, linkedkey, link_id):
        self.key = key
        self.linkedkey = linkedkey
        self.link_id = link_id
        self.url = jira_url+'/rest/api/2/issue/%s' % self.key
        self.payload = {
            "fields": {
            },
            "update": {
                "issuelinks": [{
                    "add": {
                        "type": {
                            "id":"%s" %self.link_id},
                        "outwardIssue": {
                            "key": "%s" % self.linkedkey}
                    }
                }
                ]
            }
        }
        self.response = self.session.put(self.url, data=playload.makeplayload(self.payload), headers=headers,
                                         timeout=10.0)
        logging.debug("Ticket Link done! %s main issue: %s linked issue: %s" %(self.response.status_code,self.key, self.linkedkey))
        return self.response

    def deleteLinked(self, key, issuedlink):
        self.issuedlink = issuedlink
        self.key = key
        # self.url = jira_url+'/rest/api/3/issue/%s/remotelink/%s' %(self.key,issuedlink)
        self.url = jira_url+'/rest/api/2/issueLink/%s' % issuedlink
        logging.debug('start delete linkissue:' + self.url)
        self.response = self.session.delete(self.url, headers=headers, timeout=10.0)
        # self.response = self.session.delete(self.url, data=playload.makeplayload(self.payload), headers=headers)
        logging.debug(self.response.status_code)
        logging.debug("Done: %s linked issue: %s" % (self.key, issuedlink))

    def getusername(self):
        self.url = jira_url+'/rest/gadget/1.0/currentUser'
        self.response = self.session.get(self.url, headers=headers).json()
        return self.response['username']

    def getworklogs(self, key):
        self.key = key
        self.url = jira_url+'/rest/api/2/issue/%s/worklog/' % key
        # self.response = self.session.get(self.url, headers=headers)
        self.response = self.session.get(self.url, timeout=10.0).json()
        return self.response

    def getcomment(self, key):
        self.key = key
        self.url = jira_url+'/rest/api/2/issue/%s/comment' % key
        # self.response = self.session.get(self.url, headers=headers)
        self.response = self.session.get(self.url, timeout=10.0).json()
        return self.response

    def get_attachment(self, key = 'None'):
        uploaded_file = []
        self.key_detail_info = self.searchIssueByKey(key)
        for self.file in self.key_detail_info['fields']['attachment']:
            uploaded_file.append(self.file['filename'])
        return uploaded_file

    def addcommnet(self, key, comment):
        self.key = key
        self.comment = comment
        self.url = jira_url+'/rest/api/2/issue/%s/comment' % key
        self.payload = {"body": "%s" % comment}
        # print(self.payload)
        # self.response = self.session.get(self.url, headers=headers)
        self.response = self.session.post(self.url, data=playload.makeplayload(self.payload), headers=headers,
                                          timeout=10.0)
        return self.response

    def update_label(self, key = None, label = None):
        #find label list
        exist_labels = self.searchIssueByKey(key)['fields']['labels']
        #pass if label exist in labels
        if label in exist_labels:
            logging.debug('%s is already included of labes - %s' %(label,exist_labels))
        else:
            exist_labels.append(label)
            playloads = {"fields":{"labels":''}}
            playloads['fields']['labels'] = exist_labels
            logging.debug(playloads)
            self.updateissue(key,playloads)
        return 0
    
    def getworklogdetail(self, id):
        self.id = id
        self.url = jira_url+'/rest/tempo-timesheets/3/worklogs/%s' % id
        # self.response = self.session.get(self.url, headers=headers)
        self.response = self.session.get(self.url, timeout=10.0).json()
        return self.response

    def trasit(self, key, status):
        logging.debug('get stuts')
        self.url = jira_url+'/rest/api/2/issue/%s/transitions' % key
        self.status = self.session.get(self.url, headers=headers, timeout=10.0)
        self.transitions = json.loads(self.status.text)['transitions']
        self.dict_transition = {}
        for self.transition in self.transitions:
            self.dict_transition[self.transition['to']['name']] = self.transition['id']
        logging.debug('change stuts')
        self.key = key
        self.status = status
        if self.status in self.dict_transition.keys():
            self.id = self.dict_transition[self.status]
            self.payload = {"transition": {"id": "%s" % self.id}}
            self.url = jira_url+'/rest/api/2/issue/%s/transitions?expand=transitions.fields' % self.key
            self.r = self.session.post(self.url, data=playload.makeplayload(self.payload), headers=headers,
                                       timeout=10.0)
            return self.r
    
    def upload_attachment(self, key = 'None', file='None'):
        self.url = jira_url+"/rest/api/2/issue/%s/attachments"  % key
        self.upload_file = open(file,"rb")
        self.files = {"file": self.upload_file}
        print(file)
        print(self.url)
        self.headers = {
            'Cache-Control': 'no-cache',
            'X-Atlassian-Token': 'no-check'}
        self.r = self.session.post(self.url, files=self.files, headers=self.headers)
        return self.r

    # =================================== LOG WORK =============================================

    def submitlogwork(self, key, playloads):
        self.url = jira_url+'/rest/api/2/issue/%s/worklog/' % key
        self.playload = playloads
        self.response = self.session.post(self.url, data=playload.makeplayload(self.playload), headers=headers,
                                          timeout=10.0)
        return self.response


class Handler_TestCycle():
    def __init__(self, session):
        self.session = session
        self.zephyr_headers = {
            'content-type': "application/json",
            'cache-control': "no-cache",
            'postman-token': "4fed291d-69eb-2c66-8184-acc9f8eff251"
        }

    # ==========================Test cycle===============================================================
    def getusername(self):
        self.url = jira_url+'/rest/gadget/1.0/currentUser'
        # self.response = self.session.get(self.url, headers=headers)
        self.response = self.session.get(self.url, headers=self.zephyr_headers, timeout=10.0).json()
        return self.response['username']

    def getTestCycle(self):
        # /rest/zapi/latest/execution?issueId=&projectId=&versionId=&cycleId=&offset=&action=&sorter=&expand=&limit=&folderId=
        self.type = 'version-16024-cycle-3111'
        self.url = jira_url+"/rest/zapi/latest/execution?versionId=%s" % self.type
        self.response = self.session.get(self.url, headers=self.zephyr_headers, timeout=10.0)
        print(self.response)
        print(self.response.text)

    def getExecutionInfo(self, excution_id):
        # http://localhost:2990/jira/rest/zapi/latest/execution/id?expand=
        self.url = jira_url+"/rest/zapi/latest/execution/%s?expand=" % excution_id
        self.response = self.session.get(self.url, headers=self.zephyr_headers, timeout=10.0)
        return self.response

    def updateExecution(self, excution_id=None, playloads=None):
        # http://localhost:2990/jira/rest/zapi/latest/execution/id/execute
        self.url = jira_url+"/rest/zapi/latest/execution/%s/execute" % excution_id
        self.payloads = playloads
        self.response = self.session.put(self.url, data=self.payloads,
                                         headers=self.zephyr_headers, timeout=10.0)
        return self.response

    def createTestCycle(self):
        pass

    def get_TestCase(self, key):
        self.url = jira_url+"/rest/zapi/latest/execution/%s/execute" % excution_id
        self.response = self.session.get(self.url, headers=self.zephyr_headers, timeout=10.0)
        return self.response

    def add_TestCase(self, key):
        self.key = key
        print(self.key)

    def getDefectList(self, excution_id):
        self.url = jira_url+"/rest/zapi/latest/execution/%s/defects" % excution_id
        self.response = self.session.get(self.url, headers=self.zephyr_headers, timeout=10.0)
        return self.response

    def modify_TestCase(self, key):
        self.key = key
        print(self.key)

