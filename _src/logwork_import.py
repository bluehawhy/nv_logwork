# -*- coding: utf-8 -*-
#!/usr/bin/python

from logging import log
import os
import datetime

#add internal libary

from _src._api import logger, excel, playload, config, logging_message
from _src import logwork_refer

#make logpath
logging= logger.logger

#set config
message_path = logwork_refer.message_path
config_path = logwork_refer.config_path
config_data =config.load_config(config_path)


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

def getConfigFromExcel(file):
    config_excel_data = {}
    fields_excel_data = {}
    wb = excel.Workbook(file,read_only=False,data_only=False)
    if 'config' in wb.get_sheet_list():
        config_ws = wb.get_worksheet('config')
        config_row_index = wb.get_first_row('config')
        for data in config_ws.rows:
            if data[config_row_index.index('customfieldname_excel')].value is None:
                break
            #key:value = customfieldname_excel:customfield_config
            config_excel_data[data[config_row_index.index('customfieldname_excel')].value] = str(data[config_row_index.index('customfield_config')].value)
            list_field = str(data[config_row_index.index('logwork_field')].value).split(': ')
            if len(list_field) == 2:
                fields_excel_data[list_field[0].replace('"','')]=list_field[1].replace('\\','')[1:-1]
    return fields_excel_data, config_excel_data

def link_between_task_TQAOD(rh,key1,key2):
    link_id = '10900'
    if key1 in ('None','__','0','-'):
        logging_message.input_message(path = message_path,message = "key is wrong. key name: %s" %key1)
    else:
        result = rh.createLinked(key1,key2,link_id)
        logging.info("Ticket Link done! %s main issue: %s linked issue: %s" %(result.status_code,key1, key2))
        logging_message.input_message(path = message_path,message = "Ticket Link done! %s main issue: %s linked issue: %s" %(result.status_code,key1, key2))
    return 0

def modify_excel_to_customfield(data,task_row_index,config_excel_data):
        task_excel_data ={}
        for row_data in task_row_index:
            task_excel_data[str(row_data)] = str(data[task_row_index.index(row_data)].value)
        try:
            task_excel_data['assignee']=config_data['id']
            task_excel_data['originalestimate']=str(float(task_excel_data['originalestimate']) * 480) + "m"
            task_excel_data['duedate']=task_excel_data['duedate'][0:10]+"T18:00:00.000+0900"
            task_excel_data['plannedstart']=task_excel_data['plannedstart'][0:10]+"T09:00:00.000+0900"
            task_excel_data['plannedend']=task_excel_data['plannedend'][0:10]+"T18:00:00.000+0900"
        except:
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            task_excel_data['assignee']=config_data['id']
            task_excel_data['originalestimate']=str(300) + "m"
            task_excel_data['duedate']=today_str+"T18:00:00.000+0900"
            task_excel_data['plannedstart']=today_str+"T09:00:00.000+0900"
            task_excel_data['plannedend']=today_str+"T18:00:00.000+0900"
        
        #modify feild name from excel to jira
        for task_key in list(task_excel_data.keys()):
            if task_key in config_excel_data.keys():
                new_key = config_excel_data[task_key]
                task_excel_data[new_key] = task_excel_data.pop(task_key)
        return task_excel_data

def createTask(rh, file, sheet_name='SW_TQA_makeTask'):
    # init
    logging_message.input_message(path = message_path,message = '========== create task ==========')
    logging.debug('read excel sheet')
    wb = excel.Workbook(file,read_only=False,data_only=False)
    if sheet_name in wb.get_sheet_list():
        # ===========================make task in SW_TQA_makeTask sheet===============================
        task_ws = wb.get_worksheet(sheet_name)
        task_row_index = wb.get_first_row(sheet_name)
        fields_excel_data, config_excel_data = getConfigFromExcel(file)
        #logging.info(fields_excel_data)
        #logging.info(config_excel_data)
        list_opened_tasks = makeListOpenTask(rh)
    else:
        logging_message.input_message(path = message_path,message = "there is no maketask sheet.")
        logging_message.input_message(path = message_path,message = "please check excel sheet.")
        return 0
    
    count = 0
    for data in task_ws.rows:
        count += 1
        task_excel_data = {}
        task_playloads = {}
        task_excel_data = modify_excel_to_customfield(data,task_row_index,config_excel_data)
        task_playloads = playload.make_playload(task_excel_data,config_data['logwork_field'])
        if task_excel_data['summary'] in ('None','__','0'):
            break
        if task_excel_data['summary'] == 'summary':
            continue
        if task_excel_data['summary'] in list(list_opened_tasks.values()):
            key = list(list_opened_tasks.keys())[list(list_opened_tasks.values()).index(task_excel_data['summary'])]
            logging_message.input_message(path = message_path,message = "task exists %s -> skip" % key)
            logging.info('task exists key: %s summary: %s' %(key ,task_excel_data['summary']))
            wb.chagne_cell_data(task_ws, task_row_index.index('key'), count, key)
            link_between_task_TQAOD(rh,task_excel_data['Link'],key)
        else:
            # create task
            logging_message.input_message(path = message_path,message = f"make task - {task_excel_data['summary']}")
            def create_taskss():
                ticket_result = rh.createTicket(task_playloads['input_playload'])
                ticket_create_result_code = ticket_result.status_code
                ticket_create_result_text = ticket_result.text
                logging.info(ticket_create_result_code)
                # logging task info and result
                if ticket_create_result_code !=201: # status_code != 201:
                    logging_message.input_message(path = message_path,message = f"can't make ticket status code : {ticket_create_result_code}")
                    wb.chagne_cell_data(task_ws, task_row_index.index('key'), count, ticket_create_result_text)
                    logging.debug(ticket_create_result_text)
                elif ticket_create_result_code == 201:
                    key = ticket_result.json()["key"]
                    logging.info(key)
                    logging.debug(ticket_result.json())
                    logging_message.input_message(path = message_path,message = f"create ticket {key} done!, status code : {ticket_create_result_code}")
                    wb.chagne_cell_data(task_ws, task_row_index.index('key'), count, key)
                    link_between_task_TQAOD(rh,task_excel_data['Link'],key)
                else:
                    pass
            create_taskss()
    saveworkbook(wb,file)
    wb.close_workbook()
    logging_message.input_message(path = message_path,message = "task import done!")
    return 0


def importLogwork(rh, file):
    # init
    username = rh.getusername()
    logging_message.input_message(path = message_path,message = ' ========== update logwork========== ')
    logging_message.input_message(path = message_path,message = 'start for logwork')
    wb = excel.Workbook(file,read_only=False,data_only=False)
    if 'logwork' in wb.get_sheet_list():
        # ===========================make task in MakeTask sheet===============================
        logwork_ws = wb.get_worksheet('logwork')
        logwork_row_index = wb.get_first_row('logwork')
        list_opened_tasks = makeListOpenTask(rh)
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
                logwork_playloads = playload.make_playload(logwork_excel_data,config_data['logwork_type'])['input_playload']
                logging_message.input_message(path = message_path,message = f"{logwork_excel_data['summary']}")
                def find_logwork_info(summary,logwork_time):
                    logwork_info = {}
                    key = 'no_task'
                    logwork_id = 'no_logwork'
                    #find task by summary
                    if summary in list(list_opened_tasks.values()):
                        key = list(list_opened_tasks.keys())[list(list_opened_tasks.values()).index(summary)]
                        logworks = rh.getworklogs(key)
                        for logwork in logworks['worklogs']:
                            if logwork_time in str(logwork):
                                logwork_id = logwork['id']
                    logwork_info['key'] = key
                    logwork_info['logwork_id'] = logwork_id
                    return logwork_info
                logwork_info = find_logwork_info(logwork_excel_data['summary'],logwork_excel_data['logwork_start'])
                #logging.info(logwork_info)

                #input logwork
                if logwork_info['key'] == "no_task":
                    logging.info('there is no task %s' %logwork_excel_data['summary'])
                    logging_message.input_message(path = message_path,message = 'no task please make task')
                    logging_message.input_message(path = message_path,message = f"{logwork_excel_data['summary']}")
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
                            #logging.debug(result.text)
                            logging_message.input_message(path = message_path,message = 'logwork imported! key: %s and logwork id: %s' %(logwork_info['key'],result.json()['id']))
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, result.json()['id'])
        saveworkbook(wb,file)
        wb.close_workbook()
        logging_message.input_message(path = message_path,message = "logwork import done!")
    else:
        logging_message.input_message(path = message_path,message = "there is no logwork sheet.")
        logging_message.input_message(path = message_path,message = "please check excel sheet.")