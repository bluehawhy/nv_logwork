# rest.py
# !/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2018. 11. 15.
@author: miskang
#update list
2023-07-14 : add jira url 
2023-08-04 : add login status
'''

# This script shows how to connect to a JIRA instance with a
# username and password over HTTP BASIC authentication.
import os
import sys
# import requests library for making REST calls
import json
import requests

from . import loggas
from . import jason
from . import configus

config_path = os.path.join('static','config','config.json')
config_data =configus.load_config(config_path)
logging = loggas.logger
# =============================================================================================

headers = {
    'Cache-Control': 'no-cache',
    'Accept': 'application/json;charset=UTF-8',  # default for REST
    # 'Accept': 'application/json',  # default for REST
    # 'Pragma': 'no-cache',
    # 'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'
    'Content-Type': 'application/json',  # ;charset=UTF-8',
    'X-Atlassian-Token': 'no-check'}

def initsession(username, password, jira_url = config_data['jira_url'], cert=None):
    logging.debug("start log in from rest.py")
    session = None
    session_info = None
    status_login = False
    # Create Session
    logging.debug("make session")
    session = requests.Session()
    login_url = jira_url+'/rest/auth/1/session'
    payload = {"username": username, "password": password}
    logging.debug(login_url)
    try:
        logging.debug("try log in")
        session_info = session.post(login_url, data=json.dumps(payload), headers=headers, timeout=120,cert=cert)
    except Exception as e:    # This is the correct syntax
        logging.debug("Fail to log in Reason: %s" %str(e))
        session_info = None
    else:
        if session_info.status_code == 200:
            logging.debug("log in success!")
            status_login = True
        else:
            logging.debug("Fail to log in Reason: %s" %str(session_info.text))
            logging.debug(session_info)
    return session,session_info, status_login


class Handler_Jira():
    '''docstring for Handler_Jira'''

    def __init__(self, session, jira_url):
        self.session = session
        self.jira_url = jira_url

    def searchIssueCountByQuery(self, query):
        self.all_issues = {}
        self.issue = {}
        rest_url = self.jira_url+'/rest/api/2/search?startAt=0&maxResults=1&jql=%s' %query
        self.response = self.session.get(rest_url, timeout=100.0).json()
        self.issuecount = self.response['total']
        return self.issuecount

    def searchIssueByQuery(self, query):
        self.all_issues = {}
        self.issue = {}
        rest_url = self.jira_url+'/rest/api/2/search?startAt=0&maxResults=1&jql=%s' %query
        self.response = self.session.get(rest_url, timeout=100.0).json()
        self.issuecount = self.response['total']
        #logging.debug('issue count: %s' %self.issuecount)
        self.start = 0
        self.maxResults = 1000
        while self.start <= self.issuecount:  # Spaces around !=. Makes Guido van Rossum happy.
            rest_url = self.jira_url+'/rest/api/2/search?startAt=%s&maxResults=%s&jql=%s' %(
            self.start, self.maxResults, query)
            #logging.debug(rest_url)
            self.response = self.session.get(rest_url, timeout=100.0).json()
            for self.re in self.response['issues']:
                # logging.debug(self.re)
                self.issue = {str(self.re['key']): self.re['fields']}
                self.all_issues.update(self.issue)
            self.start += 1000
        self.issues = self.all_issues
        return self.issues

    def searchIssueByKey(self, key):
        self.key = key
        rest_url = self.jira_url+'/rest/api/2/issue/%s' %self.key
        self.response = self.session.get(rest_url, timeout=10.0).json()
        return self.response

    def createTicket(self, payloads):
        # ============= init =====================
        rest_url = self.jira_url+'/rest/api/2/issue'
        self.payload = payloads
        self.response = self.session.post(rest_url, data=jason.makeplayload(self.payload), headers=headers,
                                          timeout=10.0)
        logging.debug(f'code: {self.response.status_code} // info: {json.loads(self.response.text)}')
        return self.response
    
    def update_customfield(self, key, customfield,values):
        ticket_info = self.searchIssueByKey(key)
        if type(ticket_info['fields'][customfield]) is not None:
            #no customfield so make new one.
            ticket_category_fields = {}
            ticket_category_fields['fields']={}
            ticket_category_fields["fields"][customfield] = values
            logging.debug('%s - %s' %(key,ticket_category_fields))
            self.response = self.updateissue(key,ticket_category_fields)
        else:
            #no customfield so make new one.
            ticket_category_fields = {}
            ticket_category_fields['fields']={}
            ticket_category_fields["fields"][customfield] = values
            logging.debug('%s - %s' %(key,ticket_category_fields))
            self.response = self.updateissue(key,ticket_category_fields)
        return self.response


    def updateissue(self, key, payloads):
        # update issue
        self.key = key
        rest_url = self.jira_url+'/rest/api/2/issue/%s' %self.key
        self.payload = payloads
        self.headers = headers
        # logging.debug("update url: %s" %rest_url)
        self.response = self.session.put(rest_url, data=jason.makeplayload(self.payload), headers=headers,
                                         timeout=10.0)
        logging.debug("Done: %s and code: %s" %(self.key, self.response.status_code))
        return self.response

    def createLinked(self, key, linkedkey, link_id):
        self.key = key
        self.linkedkey = linkedkey
        self.link_id = link_id
        rest_url = self.jira_url+'/rest/api/2/issue/%s' %self.key
        self.payload = {
            "fields": {
            },
            "update": {
                "issuelinks": [{
                    "add": {
                        "type": {
                            "id":"%s" %self.link_id},
                        "outwardIssue": {
                            "key": "%s" %self.linkedkey}
                    }
                }
                ]
            }
        }
        self.response = self.session.put(rest_url, data=jason.makeplayload(self.payload), headers=headers,
                                         timeout=10.0)
        logging.debug("Ticket Link done! %s main issue: %s linked issue: %s" %(self.response.status_code,self.key, self.linkedkey))
        return self.response

    def deleteLinked(self, key, issuedlink):
        self.issuedlink = issuedlink
        self.key = key
        # rest_url = jira_url+'/rest/api/3/issue/%s/remotelink/%s' %(self.key,issuedlink)
        rest_url = self.jira_url+'/rest/api/2/issueLink/%s' %issuedlink
        logging.debug('start delete linkissue:' + rest_url)
        self.response = self.session.delete(rest_url, headers=headers, timeout=10.0)
        # self.response = self.session.delete(rest_url, data=playload.makeplayload(self.payload), headers=headers)
        logging.debug(self.response.status_code)
        logging.debug("Done: %s linked issue: %s" %(self.key, issuedlink))

    def getusername(self):
        rest_url = self.jira_url+'/rest/gadget/1.0/currentUser'
        self.response = self.session.get(rest_url, headers=headers).json()
        return self.response['username']

    def getworklogs(self, key):
        self.key = key
        rest_url = self.jira_url+'/rest/api/2/issue/%s/worklog/' %key
        # self.response = self.session.get(rest_url, headers=headers)
        self.response = self.session.get(rest_url, timeout=10.0).json()
        return self.response

    def getcomment(self, key):
        self.key = key
        rest_url = self.jira_url+'/rest/api/2/issue/%s/comment' %key
        # self.response = self.session.get(rest_url, headers=headers)
        self.response = self.session.get(rest_url, timeout=10.0).json()
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
        rest_url = self.jira_url+'/rest/api/2/issue/%s/comment' %key
        self.payload = {"body": "%s" %comment}
        # logging.debug(self.payload)
        # self.response = self.session.get(rest_url, headers=headers)
        self.response = self.session.post(rest_url, data=jason.makeplayload(self.payload), headers=headers,
                                          timeout=10.0)
        return self.response

    def update_label(self, key = None, label = None):
        #logging.info(self.searchIssueByKey(key))
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
    
    def delete_label(self, key = None, label = None):
        #find label list
        exist_labels = self.searchIssueByKey(key)['fields']['labels']
        #pass if label exist in labels
        if label in exist_labels:
            logging.debug(f'{exist_labels} - so remove {label}')
            exist_labels.remove(label)
            playloads = {"fields":{"labels":''}}
            playloads['fields']['labels'] = exist_labels
            logging.debug(playloads)
            self.updateissue(key,playloads)
        else:
            logging.debug(f'{label} is not included of labes - {exist_labels}')
        return 0
    
    def getworklogdetail(self, id):
        self.id = id
        rest_url = self.jira_url+'/rest/tempo-timesheets/3/worklogs/%s' %id
        # self.response = self.session.get(rest_url, headers=headers)
        self.response = self.session.get(rest_url, timeout=10.0).json()
        return self.response

    def trasit(self, key, status):
        logging.debug('get stuts')
        rest_url = self.jira_url+'/rest/api/2/issue/%s/transitions' %key
        self.status = self.session.get(rest_url, headers=headers, timeout=10.0)
        self.transitions = json.loads(self.status.text)['transitions']
        self.dict_transition = {}
        for self.transition in self.transitions:
            self.dict_transition[self.transition['to']['name']] = self.transition['id']
        logging.debug('change stuts')
        self.key = key
        self.status = status
        if self.status in self.dict_transition.keys():
            self.id = self.dict_transition[self.status]
            self.payload = {"transition": {"id": "%s" %self.id}}
            rest_url = self.jira_url+'/rest/api/2/issue/%s/transitions?expand=transitions.fields' %self.key
            self.r = self.session.post(rest_url, data=jason.makeplayload(self.payload), headers=headers,
                                       timeout=10.0)
            return self.r
    
    def upload_attachment(self, key = 'None', file='None'):
        rest_url = self.jira_url+"/rest/api/2/issue/%s/attachments"  %key
        self.upload_file = open(file,"rb")
        self.files = {"file": self.upload_file}
        logging.debug(file)
        logging.debug(rest_url)
        self.headers = {
            'Cache-Control': 'no-cache',
            'X-Atlassian-Token': 'no-check'}
        self.r = self.session.post(rest_url, files=self.files, headers=self.headers)
        return self.r


    def web_link(self, key = None, title = None, url = None):
        self.key = key
        rest_url = self.jira_url+'/rest/api/2/issue/%s/remotelink' %self.key
        self.response = self.session.get(rest_url, timeout=10.0).json()
        if url in str(self.response):
            logging.debug(f'url already linked - {url}')
            return json.dumps({})
        else:
            self.playload = {
                "object": {"url": "%s" %url,"title": "%s" %title}
                    }
            url = f'{self.jira_url}/rest/api/2/issue/{key}/remotelink'
            self.r = self.session.post(url, data=jason.makeplayload(self.playload), headers=headers,
                                            timeout=10.0)
            return self.r

    # =================================== LOG WORK =============================================

    def submitlogwork(self, key, playloads):
        rest_url = self.jira_url+'/rest/api/2/issue/%s/worklog/' %key
        self.playload = playloads
        self.response = self.session.post(rest_url, data=jason.makeplayload(self.playload), headers=headers,
                                          timeout=10.0)
        return self.response



class Handler_TestCycle():
    def __init__(self, session, jira_url):
        self.session = session
        self.zephyr_headers = {
            'content-type': "application/json",
            'cache-control': "no-cache",
            'postman-token': "4fed291d-69eb-2c66-8184-acc9f8eff251"
        }
        self.jira_url = jira_url

    # ==========================Test cycle===============================================================
    def getusername(self):
        rest_url = self.jira_url+'/rest/gadget/1.0/currentUser'
        # self.response = self.session.get(rest_url, headers=headers)
        self.response = self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0).json()
        return self.response['username']

    
    def get_test_execution_by_query(self, test_execution_query):
        #http://localhost:2990/jira/rest/zapi/latest/zql/executeSearch?zqlQuery=&filterId=&offset=&maxRecords=&expand=
        rest_url = self.jira_url+'/rest/zapi/latest/zql/executeSearch?zqlQuery=folderId=7894&cycleId=7008'
        rest_url = self.jira_url+'/rest/zapi/latest/zql/executeSearch?zqlQuery=id="1604554"'
        rest_url = self.jira_url+'/rest/zapi/latest/zql/executeSearch?zqlQuery=%s' %test_execution_query
        logging.info(rest_url)
        self.response = self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)
        logging.debug(self.response)
        return self.response

    def get_test_execution_by_id(self, excution_id):
        # http://localhost:2990/jira/rest/zapi/latest/execution/id?expand=
        rest_url = self.jira_url+ f"/rest/zapi/latest/execution/{excution_id}?expand="
        self.response = self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)
        return self.response


    def update_test_execution(self, excution_id=None, playloads=None):
        # http://localhost:2990/jira/rest/zapi/latest/execution/id/execute
        rest_url = self.jira_url+ f"/rest/zapi/latest/execution/{excution_id}/execute"
        self.payloads = playloads
        self.response = self.session.put(rest_url, data=self.payloads,headers=self.zephyr_headers, timeout=10.0)
        return self.response
    
    def update_test_step(self,stepid= None, playloads=None):
        rest_url = self.jira_url+"/rest/zapi/latest/stepResult/%s" %stepid
        self.payloads = playloads
        self.response = self.session.put(rest_url, data=self.payloads,headers=self.zephyr_headers, timeout=10.0)
        return self.response

    def get_test_cycle_info(self, cycle_id):
        #http://localhost:2990/jira/rest/zapi/latest/cycle/id
        rest_url = self.jira_url+'/rest/zapi/latest/cycle/%s' %cycle_id
        logging.info(rest_url)
        self.response = self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)
        logging.debug(self.response)
        return self.response

    def get_folder_from_test_cycle_id(self, cycle_id):
        #CycleResource/Get 
        # the list of folder for a cycle/Get the list of folder for a cycle
        # GET 
        # http://localhost:2990/jira/rest/zapi/latest/cycle/{cycleId}/folders?projectId=&versionId=&limit=&offset=
        #get project id and version id 
        self.test_cycle_info = self.get_test_cycle_info(cycle_id=cycle_id)
        self.test_cycle_info = jason.make_json(self.test_cycle_info.text)
        self.project_id = self.test_cycle_info['projectId']
        self.version_id = self.test_cycle_info['versionId']
        rest_url = self.jira_url+ f'/rest/zapi/latest/cycle/{cycle_id}/folders?projectId={self.project_id}&versionId={self.version_id}&limit=&offset='
        logging.info(rest_url)
        self.response = self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)
        logging.debug(self.response)
        return self.response

    def move_test_execution_into_folder(self, cycle_id, folder_id):
        # selected executions or all executions from cycle to folder
        #PUT http://localhost:2990/jira/rest/zapi/latest/cycle/{cycleId}/move/executions/folder/{folderId}
        rest_url = self.jira_url+f"/rest/zapi/latest/cycle/{cycle_id}/move/executions/folder/{folder_id}"
        logging.info(rest_url)
        self.payloads = {
            "projectId":11801,
            "versionId":20185, 
            "schedulesList":[]
            }
        self.response = self.session.put(rest_url,data=jason.makeplayload(self.payloads),headers=self.zephyr_headers, timeout=10.0)
        logging.debug(self.response.text)
        return self.response


#===============================================================================================================

    def move_test_execution(self):
        #http://localhost:2990/jira/rest/zapi/latest/cycle/{id}/move
        return 0

    def get_all_execution_by_test_zephyr(self, key):
        rest_url = self.jira_url+"/rest/zapi/latest/execution/%s/execute" %key
        self.response = self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)
        return self.response

    def createFolder(self, cycle_id ,folder_name, description ,project_id, version_id):
        #http://localhost:2990/jira/rest/zapi/latest/folder/create
        rest_url = self.jira_url+"/rest/zapi/latest/folder/create"
        self.payloads = {
            "cycleId": cycle_id,
            "name": folder_name,
            "description": description,
            "projectId": project_id,
            "versionId": version_id,
            "clonedFolderId": -1
            }
        self.response = self.session.post(rest_url, data=jason.makeplayload(self.payloads),headers=self.zephyr_headers, timeout=10.0)
        logging.debug(self.response)
        return self.response

    def t4aet(self):
        pass

    def add_TestCase(self, key):
        self.key = key
        logging.debug(self.key)

    def getDefectList(self, excution_id):
        rest_url = self.jira_url+"/rest/zapi/latest/execution/%s/defects" %excution_id
        self.response = self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)
        return self.response

    def modify_TestCase(self, key):
        self.key = key
        logging.debug(self.key)

