#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2018. 11. 15.
@author: miskang
#update list
2023-07-14 : add jira url 
2023-08-04 : add login status
2026-07-13 : 리팩토링 (self 안티패턴 수정, f-string 적용, 중복 코드 제거)
'''

import os
import requests

from . import loggas
from . import jason
from . import configus

config_path = os.path.join('static', 'config', 'config.json')
config_data = configus.load_config(config_path)
logging = loggas.logger

# 공통 헤더 정의
HEADERS = {
    'Cache-Control': 'no-cache',
    'Accept': 'application/json;charset=UTF-8',
    'Content-Type': 'application/json',
    'X-Atlassian-Token': 'no-check'
}

def initsession(username, password, jira_url=config_data['jira_url'], cert=None):
    logging.debug("start log in from rest.py")
    session = requests.Session()
    login_url = f"{jira_url}/rest/auth/1/session"
    payload = {"username": username, "password": password}
    
    status_login = False
    try:
        logging.info("try log in")
        session_info = session.post(login_url, json=payload, headers=HEADERS, timeout=120, cert=cert)
        if session_info.status_code == 200:
            logging.debug("log in success!")
            status_login = True
        else:
            logging.debug(f"Fail to log in Reason: {session_info.text}")
    except Exception as e:
        logging.debug(f"Fail to log in Reason: {str(e)}")
        session_info = None

    return session, session_info, status_login


class Handler_Jira:
    '''Jira REST API를 핸들링하는 클래스'''

    def __init__(self, session, jira_url):
        self.session = session
        self.jira_url = jira_url

    def searchIssueCountByQuery(self, query):
        rest_url = f"{self.jira_url}/rest/api/2/search?startAt=0&maxResults=1&jql={query}"
        response = self.session.get(rest_url, headers=HEADERS, timeout=100.0).json()
        return response.get('total', 0)

    def searchIssueByQuery(self, query):
        issuecount = self.searchIssueCountByQuery(query)
        all_issues = {}
        start = 0
        max_results = 1000

        while start <= issuecount:
            rest_url = f"{self.jira_url}/rest/api/2/search?startAt={start}&maxResults={max_results}&jql={query}"
            response = self.session.get(rest_url, headers=HEADERS, timeout=100.0).json()
            
            for issue in response.get('issues', []):
                all_issues[str(issue['key'])] = issue['fields']
            start += max_results

        return all_issues

    def searchIssueByKey(self, key):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}"
        return self.session.get(rest_url, headers=HEADERS, timeout=10.0).json()

    def createTicket(self, payloads):
        rest_url = f"{self.jira_url}/rest/api/2/issue"
        # 외부 jason 모듈 의존성을 유지하되, 필요 시 json=payloads 로 대체 가능합니다.
        response = self.session.post(rest_url, data=jason.makeplayload(payloads), headers=HEADERS, timeout=10.0)
        logging.debug(f'code: {response.status_code} // info: {response.text}')
        return response
    
    def update_customfield(self, key, customfield, values):
        # 기존 if-else의 중복 로직을 제거하여 깔끔하게 정리했습니다.
        ticket_category_fields = {
            "fields": {
                customfield: values
            }
        }
        logging.debug(f'{key} - {ticket_category_fields}')
        return self.updateissue(key, ticket_category_fields)

    def updateissue(self, key, payloads):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}"
        response = self.session.put(rest_url, data=jason.makeplayload(payloads), headers=HEADERS, timeout=10.0)
        logging.debug(f"Done: {key} and code: {response.status_code}")
        return response

    def createLinked(self, key, linkedkey, link_id):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}"
        payload = {
            "fields": {},
            "update": {
                "issuelinks": [{
                    "add": {
                        "type": {"id": str(link_id)},
                        "outwardIssue": {"key": str(linkedkey)}
                    }
                }]
            }
        }
        response = self.session.put(rest_url, data=jason.makeplayload(payload), headers=HEADERS, timeout=10.0)
        logging.debug(f"Ticket Link done! {response.status_code} main issue: {key} linked issue: {linkedkey}")
        return response

    def deleteLinked(self, key, issuedlink):
        rest_url = f"{self.jira_url}/rest/api/2/issueLink/{issuedlink}"
        logging.debug(f'start delete linkissue: {rest_url}')
        response = self.session.delete(rest_url, headers=HEADERS, timeout=10.0)
        logging.debug(f"Done: {key} linked issue: {issuedlink} | Status: {response.status_code}")
        return response

    def getusername(self):
        rest_url = f"{self.jira_url}/rest/gadget/1.0/currentUser"
        response = self.session.get(rest_url, headers=HEADERS).json()
        return response.get('username')

    def getworklogs(self, key):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}/worklog/"
        return self.session.get(rest_url, headers=HEADERS, timeout=10.0).json()

    def getcomment(self, key):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}/comment"
        return self.session.get(rest_url, headers=HEADERS, timeout=10.0).json()

    def get_attachment(self, key='None'):
        ticket_info = self.searchIssueByKey(key)
        attachments = ticket_info.get('fields', {}).get('attachment', [])
        return [f['filename'] for f in attachments]

    def addcommnet(self, key, comment):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}/comment"
        payload = {"body": str(comment)}
        return self.session.post(rest_url, data=jason.makeplayload(payload), headers=HEADERS, timeout=10.0)

    def update_label(self, key=None, label=None):
        if not key or not label:
            return 0
        exist_labels = self.searchIssueByKey(key).get('fields', {}).get('labels', [])
        
        if label in exist_labels:
            logging.debug(f'{label} is already included in labels - {exist_labels}')
        else:
            exist_labels.append(label)
            payloads = {"fields": {"labels": exist_labels}}
            logging.debug(payloads)
            self.updateissue(key, payloads)
        return 0
    
    def delete_label(self, key=None, label=None):
        if not key or not label:
            return 0
        exist_labels = self.searchIssueByKey(key).get('fields', {}).get('labels', [])
        
        if label in exist_labels:
            logging.debug(f'{exist_labels} - so remove {label}')
            exist_labels.remove(label)
            payloads = {"fields": {"labels": exist_labels}}
            logging.debug(payloads)
            self.updateissue(key, payloads)
        else:
            logging.debug(f'{label} is not included in labels - {exist_labels}')
        return 0
    
    def getworklogdetail(self, worklog_id):
        rest_url = f"{self.jira_url}/rest/tempo-timesheets/3/worklogs/{worklog_id}"
        return self.session.get(rest_url, headers=HEADERS, timeout=10.0).json()

    def trasit(self, key, status):
        logging.debug('get status')
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}/transitions"
        status_response = self.session.get(rest_url, headers=HEADERS, timeout=10.0)
        transitions = status_response.json().get('transitions', [])
        
        dict_transition = {t['to']['name']: t['id'] for t in transitions}
        
        logging.debug('change status')
        if status in dict_transition:
            transition_id = dict_transition[status]
            payload = {"transition": {"id": str(transition_id)}}
            transit_url = f"{self.jira_url}/rest/api/2/issue/{key}/transitions?expand=transitions.fields"
            return self.session.post(transit_url, data=jason.makeplayload(payload), headers=HEADERS, timeout=10.0)
        else:
            logging.debug(f"Status '{status}' not found in available transitions.")
            return None
    
    def upload_attachment(self, key='None', file_path='None'):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}/attachments"
        logging.debug(file_path)
        
        upload_headers = {
            'Cache-Control': 'no-cache',
            'X-Atlassian-Token': 'no-check'
        }
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = self.session.post(rest_url, files=files, headers=upload_headers)
        return response

    def web_link(self, key=None, title=None, url=None):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}/remotelink"
        response_text = self.session.get(rest_url, headers=HEADERS, timeout=10.0).text
        
        if url in response_text:
            logging.debug(f'url already linked - {url}')
            return {"message": "already linked"}
        
        payload = {"object": {"url": str(url), "title": str(title)}}
        return self.session.post(rest_url, data=jason.makeplayload(payload), headers=HEADERS, timeout=10.0)

    def submitlogwork(self, key, payloads):
        rest_url = f"{self.jira_url}/rest/api/2/issue/{key}/worklog/"
        return self.session.post(rest_url, data=jason.makeplayload(payloads), headers=HEADERS, timeout=10.0)


class Handler_TestCycle:
    def __init__(self, session, jira_url):
        self.session = session
        self.jira_url = jira_url
        self.zephyr_headers = {
            'content-type': "application/json",
            'cache-control': "no-cache"
        }

    def getusername(self):
        rest_url = f"{self.jira_url}/rest/gadget/1.0/currentUser"
        response = self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0).json()
        return response.get('username')
    
    def get_test_execution_by_query(self, test_execution_query):
        rest_url = f"{self.jira_url}/rest/zapi/latest/zql/executeSearch?zqlQuery={test_execution_query}"
        logging.info(rest_url)
        return self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)

    def get_test_execution_by_id(self, execution_id):
        rest_url = f"{self.jira_url}/rest/zapi/latest/execution/{execution_id}?expand="
        return self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)

    def update_test_execution(self, execution_id=None, payloads=None):
        rest_url = f"{self.jira_url}/rest/zapi/latest/execution/{execution_id}/execute"
        return self.session.put(rest_url, data=payloads, headers=self.zephyr_headers, timeout=10.0)
    
    def update_test_step(self, stepid=None, payloads=None):
        rest_url = f"{self.jira_url}/rest/zapi/latest/stepResult/{stepid}"
        return self.session.put(rest_url, data=payloads, headers=self.zephyr_headers, timeout=10.0)

    def get_test_cycle_info(self, cycle_id):
        rest_url = f"{self.jira_url}/rest/zapi/latest/cycle/{cycle_id}"
        logging.info(rest_url)
        return self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)

    def get_folder_from_test_cycle_id(self, cycle_id):
        test_cycle_response = self.get_test_cycle_info(cycle_id=cycle_id)
        test_cycle_info = jason.make_json(test_cycle_response.text)
        
        project_id = test_cycle_info.get('projectId')
        version_id = test_cycle_info.get('versionId')
        
        rest_url = f'{self.jira_url}/rest/zapi/latest/cycle/{cycle_id}/folders?projectId={project_id}&versionId={version_id}&limit=&offset='
        logging.info(rest_url)
        return self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)

    def move_test_execution_into_folder(self, cycle_id, folder_id):
        rest_url = f"{self.jira_url}/rest/zapi/latest/cycle/{cycle_id}/move/executions/folder/{folder_id}"
        logging.info(rest_url)
        payloads = {
            "projectId": 11801,
            "versionId": 20185, 
            "schedulesList": []
        }
        return self.session.put(rest_url, data=jason.makeplayload(payloads), headers=self.zephyr_headers, timeout=10.0)

    def get_all_execution_by_test_zephyr(self, key):
        rest_url = f"{self.jira_url}/rest/zapi/latest/execution/{key}/execute"
        return self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)

    def createFolder(self, cycle_id, folder_name, description, project_id, version_id):
        rest_url = f"{self.jira_url}/rest/zapi/latest/folder/create"
        payloads = {
            "cycleId": cycle_id,
            "name": folder_name,
            "description": description,
            "projectId": project_id,
            "versionId": version_id,
            "clonedFolderId": -1
        }
        return self.session.post(rest_url, data=jason.makeplayload(payloads), headers=self.zephyr_headers, timeout=10.0)

    def getDefectList(self, execution_id):
        rest_url = f"{self.jira_url}/rest/zapi/latest/execution/{execution_id}/defects"
        return self.session.get(rest_url, headers=self.zephyr_headers, timeout=10.0)