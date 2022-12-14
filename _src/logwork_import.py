# -*- coding: utf-8 -*-
#!/usr/bin/python

from logging import log
import os
import datetime

#add internal libary

from _src._api import rest, logger, excel, playload, config, logging_message
from _src import logwork_refer

#make logpath
logging= logger.logger

#set config
message_path = logwork_refer.message_path
config_path = logwork_refer.config_path
task_config =config.load_config(config_path)['task_type']
logwork_config =config.load_config(config_path)['logwork_type']

#logging_message.input_message(path = message_path,message = 'license info: '+ str(self.license))

def saveworkbook(wb,file):
    try:
        wb.save_workbook(file)
    except PermissionError:
        logging_message.input_message(path = message_path,message = 'your excel sheet has been opened')
        logging_message.input_message(path = message_path,message = 'new sheet has been saved as the path : %s ' %str(file).replace('.xlsx','_temp.xlsx'))
        wb.save_workbook(str(file).replace('.xlsx','_temp.xlsx'))

def makeListOpenTask(rh):
    # ===========================get task list in jira===============================
    logging.info('get task list from Jira')
    issues = rh.searchIssueByQuery(
        'project = TQA_OD and reporter = currentUser() and status not in (Resolved,Closed,Cancelled)')
    list_task = {}
    for issue in issues:
        key = issue
        summary = issues[issue]['summary']
        list_task[key] = summary
    return list_task

def makeLink(key1,key2):
    return 0

def getConfigFromExcel(file):
    config_excel_data = {}
    wb = excel.Workbook(file,read_only=False,data_only=False)
    if 'config' in wb.get_sheet_list():
        config_ws = wb.get_worksheet('config')
        config_row_index = wb.get_first_row('config')
        for data in config_ws.rows:
            #key:value = customfieldname_excel:customfield_config
            config_excel_data[data[config_row_index.index('customfieldname_excel')].value] = str(data[config_row_index.index('customfield_config')].value)
        #logging.debug(config_excel_data)
    return config_excel_data


def createTask(rh, file):
    # init
    username = rh.getusername()
    logging_message.input_message(path = message_path,message = '==================================================== create task ====================================================')
    logging.debug('read excel sheet')
    wb = excel.Workbook(file,read_only=False,data_only=False)
    if 'makeTask' in wb.get_sheet_list():
        # ===========================make task in MakeTask sheet===============================
        task_ws = wb.get_worksheet('makeTask')
        task_row_index = wb.get_first_row('makeTask')
        list_tasks = makeListOpenTask(rh)
        count = 0
        for data in task_ws.rows:
            count += 1
            task_playloads = {}
            task_excel_data ={}
            #input value from excel to task_excel_data
            for row_data in task_row_index:
                task_excel_data[str(row_data)] = str(data[task_row_index.index(row_data)].value)
            #modify task_excel_data
            def modify_task_excel():
                task_excel_data['assignee']=username
                task_excel_data['originalestimate']=str(float(task_excel_data['originalestimate']) * 480) + "m"
                task_excel_data['duedate']=task_excel_data['duedate'][0:10]+"T18:00:00.000+0900"
                task_excel_data['plannedstart']=task_excel_data['plannedstart'][0:10]+"T09:00:00.000+0900"
                task_excel_data['plannedend']=task_excel_data['plannedend'][0:10]+"T18:00:00.000+0900"
            try:
                modify_task_excel()
            except:
                logging.info('there is parsing error for originalestimate and due date')
                pass
            change_key_dict = getConfigFromExcel(file)
            for task_key in list(task_excel_data.keys()):
                    if task_key in change_key_dict.keys():
                        new_key = change_key_dict[task_key]
                        task_excel_data[new_key] = task_excel_data.pop(task_key)
           
            def link_between_task_TQAOD(key1,key2):
                link_id = '10900'
                if key1 in ('None','__','0','-'):
                    logging_message.input_message(path = message_path,message = "key is wrong. key name: %s" %key1)
                else:
                    result = rh.createLinked(key1,key2,link_id)
                    logging.info("Ticket Link done! %s main issue: %s linked issue: %s" %(result.status_code,key1, key2))
                    logging_message.input_message(path = message_path,message = "Ticket Link done! %s main issue: %s linked issue: %s" %(result.status_code,key1, key2))
                
            #check summary value
            if task_excel_data['summary'] in ('None','__','0'):
                break
            if task_excel_data['summary'] == 'summary':
                pass
            else:
            # check task exist -> get a key and input excel sheet
                if task_excel_data['summary'] in list(list_tasks.values()):
                    key = list(list_tasks.keys())[list(list_tasks.values()).index(task_excel_data['summary'])]
                    logging_message.input_message(path = message_path,message = "task exists %s -> skip" % key)
                    logging.info('task exists key: %s summary: %s' %(key ,task_excel_data['summary']))
                    wb.chagne_cell_data(task_ws, task_row_index.index('key'), count, key)
                    link_between_task_TQAOD(task_excel_data['Link'],key)
                else:
                    # create task
                    task_playloads = playload.make_playload(task_excel_data,task_config)['input_playload']
                    logging.debug(task_excel_data)
                    logging.debug(task_playloads)
                    logging_message.input_message(path = message_path,message = "%s not exists -> make task" % task_excel_data['summary'])
                    ticket_result = rh.createTicket(task_playloads)
                    ticket_create_result_code = ticket_result.status_code
                    ticket_create_result_text = ticket_result.text
                    logging.info(ticket_create_result_code)
                    # logging task info and result
                    if ticket_create_result_code !=201: # status_code != 201:
                        logging_message.input_message(path = message_path,message = "can't make ticket %s , status code : %s\n" % (task_excel_data['summary'], ticket_create_result_code))
                        wb.chagne_cell_data(task_ws, task_row_index.index('key'), count, ticket_create_result_text)
                        logging.debug('task_excel_data is %s' %str(task_excel_data))
                        logging.debug('task_playlaods is %s' %str(task_playloads))
                        logging.debug(ticket_create_result_text)
                    elif ticket_create_result_code == 201:
                        key = ticket_result.json()["key"]
                        logging.info(key)
                        logging.debug(ticket_result.json())
                        logging_message.input_message(path = message_path,message = "create ticket %s done!, status code : %s" % (key, ticket_create_result_code))
                        wb.chagne_cell_data(task_ws, task_row_index.index('key'), count, key)
                        link_between_task_TQAOD(task_excel_data['Link'],key)
                    else:
                        pass
        saveworkbook(wb,file)
        wb.close_workbook()
        logging_message.input_message(path = message_path,message = "task import done!")
    else:
        logging_message.input_message(path = message_path,message = "there is no maketask sheet.")
        logging_message.input_message(path = message_path,message = "please check excel sheet.")

def importLogwork(rh, file):
    # init
    username = rh.getusername()
    logging_message.input_message(path = message_path,message = ' ==================================================== update logwork==================================================== ')
    wb = excel.Workbook(file,read_only=False,data_only=False)
    if 'logwork' in wb.get_sheet_list():
        # ===========================make task in MakeTask sheet===============================
        logwork_ws = wb.get_worksheet('logwork')
        logwork_row_index = wb.get_first_row('logwork')
        list_tasks = makeListOpenTask(rh)
        count = 0
        for data in logwork_ws.rows:
            count += 1  # must set correct key value in excel (index start at 1)
            logwork_playloads = {}
            logwork_excel_data ={}
            #input value from excel to task_excel_data
            for row_data in logwork_row_index:
                logwork_excel_data[str(row_data)] = str(data[logwork_row_index.index(row_data)].value)
            def modify_logwork_excel():
                logwork_excel_data['logwork_start'] = logwork_excel_data['date'][0:10]  + "T" + str(logwork_excel_data['start']) + ".000+0900"
                logwork_excel_data['spent_second'] = str(int((datetime.datetime.strptime(logwork_excel_data['end'],'%H:%M:%S') - datetime.datetime.strptime(logwork_excel_data['start'], '%H:%M:%S')).total_seconds()))
                logwork_excel_data['user'] = username
            try:
                modify_logwork_excel()
            except:
                pass
            #check summary value
            if logwork_excel_data['summary'] in ('None','__','0'):
                break
            if logwork_excel_data['summary'] == 'summary':
                pass
            else:
                logwork_playloads = playload.make_playload(logwork_excel_data,logwork_config)['input_playload']
                logging.debug(logwork_excel_data)
                logging.debug(logwork_playloads)
                logging_message.input_message(path = message_path,message = 'start for logwork %s' %logwork_excel_data['summary'])
                def find_logwork_info(summary,logwork_time):
                    logwork_info = {}
                    key = 'no_task'
                    logwork_id = 'no_logwork'
                    #find task by summary
                    if summary in list(list_tasks.values()):
                        key = list(list_tasks.keys())[list(list_tasks.values()).index(summary)]
                        logworks = rh.getworklogs(key)
                        for logwork in logworks['worklogs']:
                            if logwork_time in str(logwork):
                                logwork_id = logwork['id']
                    logwork_info['key'] = key
                    logwork_info['logwork_id'] = logwork_id
                    return logwork_info
                logwork_info = find_logwork_info(logwork_excel_data['summary'],logwork_excel_data['logwork_start'])
                logging.info(logwork_info)

                #input logwork
                if logwork_info['key'] == "no_task":
                    logging.info('there is no task %s' %logwork_excel_data['summary'])
                    logging_message.input_message(path = message_path,message = "the summary doesn't exist in task: %s " %logwork_excel_data['summary'])
                    logging_message.input_message(path = message_path,message = 'please make task')
                    wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                    wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, logwork_info['logwork_id'])
                else:
                    if logwork_info['logwork_id'] != 'no_logwork':
                        logging.info('logwork already exists -%s / %s' % (logwork_info['key'], logwork_info['logwork_id']))
                        logging_message.input_message(path = message_path,message = 'logwork already exists -%s / %s\n' % (logwork_info['key'], logwork_info['logwork_id']))
                        wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                        wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, logwork_info['logwork_id'])
                    else:
                        result = rh.submitlogwork(logwork_info['key'], logwork_playloads)
                        if result.status_code != 201:
                            logging_message.input_message(path = message_path,message = 'there is a error, refer to the message in excel')
                            logging.info('error reasion : %s' %result.text)
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, result.text)
                        else:
                            logging.debug(result.text)
                            logging_message.input_message(path = message_path,message = 'logwork imported! key: %s and logwork id: %s' %(logwork_info['key'],result.json()['id']))
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, result.json()['id'])
        saveworkbook(wb,file)
        wb.close_workbook()
        logging_message.input_message(path = message_path,message = "logwork import done!")
    else:
        logging_message.input_message(path = message_path,message = "there is no logwork sheet.")
        logging_message.input_message(path = message_path,message = "please check excel sheet.")