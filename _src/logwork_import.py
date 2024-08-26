# -*- coding: utf-8 -*-
#!/usr/bin/python

import os, sys, ast
import datetime

#add internal libary
refer_api = "local"
refer_api = "global"

if refer_api == "global":
    sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
    from _api import loggas, excelium, jason, configus
if refer_api == "local":
    from _src._api import loggas, excelium, jason, configus

#make logpath
logging= loggas.logger

#set config
message_path = '_logs\output.txt'
config_path = os.path.join('static','config','config.json')
qss_path = os.path.join('static','css','style.qss')
config_data =configus.load_config(config_path)

#======================= Common ===============================================
def check_ticket_list_in_jira(rh):
    logging.info('get task list from Jira')
    issues = rh.searchIssueByQuery(
        'project = TQA_OD and reporter = currentUser() and status not in (Resolved,Closed,Cancelled)')
    list_task = {}
    for issue in issues:
        key = issue
        summary = issues[issue]['summary']
        list_task[key] = summary
    return list_task

def make_dict_from_string(string):
    try:
        converted = ast.literal_eval(string)
        if isinstance(converted, dict):
            return converted
        if isinstance(converted, list):
            return converted
        else:
            return string
    except (SyntaxError, ValueError):
        return string

#======================= create ticket ===============================================
def link_between_task_TQAOD(rh,key1,key2):
    link_id = '10900'
    if key1 in ('None','__','0','-'):
        loggas.input_message(path = message_path,message = "key is wrong. key name: %s" %key1)
    else:
        result = rh.createLinked(key1,key2,link_id)
        logging.info("Ticket Link done! %s main issue: %s linked issue: %s" %(result.status_code,key1, key2))
        loggas.input_message(path = message_path,message = "Ticket Link done! %s main issue: %s linked issue: %s" %(result.status_code,key1, key2))
    return 0

def modify_data(execl_data, task_row_index):
    task_excel_data = {}
    for row_data in task_row_index:
        task_excel_data[str(row_data)] = str(execl_data[task_row_index.index(row_data)].value)
    task_excel_data['assignee']=config_data['id']
    try:
        task_excel_data['originalestimate']=str(float(task_excel_data['originalestimate']) * 480) + "m"
        task_excel_data['duedate']=task_excel_data['duedate'][0:10]+"T18:00:00.000+0900"
        task_excel_data['plannedstart']=task_excel_data['plannedstart'][0:10]+"T09:00:00.000+0900"
        task_excel_data['plannedend']=task_excel_data['plannedend'][0:10]+"T18:00:00.000+0900"
    #if execl data format is wrong.
    except:
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        task_excel_data['originalestimate']=str(300) + "m"
        task_excel_data['duedate']=today_str+"T18:00:00.000+0900"
        task_excel_data['plannedstart']=today_str+"T09:00:00.000+0900"
        task_excel_data['plannedend']=today_str+"T18:00:00.000+0900"
    return task_excel_data

def maapping_data(task_excel_data):
    ticket_import_data = {"fields":{}}
    # load ticket mapping data
    mapping_data =configus.load_config(os.path.join('static','config','field_mapping.json'))
    task_field = mapping_data['task_field']
    task_field_mapping = mapping_data['task_field_mapping']
    for field_key in task_field.keys():
        mapping_key = task_field_mapping[field_key]
        if mapping_key in task_excel_data.keys():
            excel_value = task_excel_data[task_field_mapping[field_key]]
            if excel_value != '0':
                replace_value = str(task_field[field_key]).replace('-',excel_value)
                replace_value = make_dict_from_string(replace_value)
                #logging.info(f'{field_key} - {excel_value} {replace_value}')
                ticket_import_data["fields"][field_key] = replace_value
        #logging.info(task_excel_data)
    #logging.info(f'{ticket_import_data}')
    return ticket_import_data

def createTask(rh, file, sheet_name='SW_TQA_makeTask'):
    #get ticket list
    list_opened_tasks = check_ticket_list_in_jira(rh)
    #logging.info(list_opened_tasks)

    # init
    loggas.input_message(path = message_path,message = '========== create task ==========')
    logging.debug('read excel sheet')
    wb = excelium.Workbook(file,read_only=False,data_only=False)
    if sheet_name not in wb.get_sheet_list():
        loggas.input_message(path = message_path,message = "there is no maketask sheet.")
        loggas.input_message(path = message_path,message = "please check excel sheet.")
        return 0
    
    # load worksheet
    task_ws = wb.get_worksheet(sheet_name)
    task_row_index = wb.get_first_row(sheet_name)
    #logging.info(task_row_index)

    count = 0
    for data in task_ws.rows:
        count += 1
        task_excel_data = {}
        summary = data[task_row_index.index('summary')].value
        if summary is None:
            return 0
        if summary != 'summary':
            #make date for import
            task_excel_data = modify_data(data,task_row_index)
            ticket_import_data = maapping_data(task_excel_data)
            logging.info(ticket_import_data)
            #=============================================
            # write key when ticket already exist
            if task_excel_data['summary'] in list(list_opened_tasks.values()):
                key = list(list_opened_tasks.keys())[list(list_opened_tasks.values()).index(task_excel_data['summary'])]
                loggas.input_message(path = message_path,message = "task exists %s -> skip" % key)
                logging.info('task exists key: %s summary: %s' %(key ,task_excel_data['summary']))
                wb.change_cell_data(task_ws, task_row_index.index('key')+1, count, key)
                link_between_task_TQAOD(rh,task_excel_data['Link'],key)
            # create task
            else:
                loggas.input_message(path = message_path,message = f"make task - {task_excel_data['summary']}")
                ticket_result = rh.createTicket(ticket_import_data)
                ticket_create_result_code = ticket_result.status_code
                ticket_create_result_text = ticket_result.text
                logging.info(ticket_create_result_code)
                # logging task info and result
                if ticket_create_result_code !=201: # status_code != 201:
                    loggas.input_message(path = message_path,message = f"can't make ticket status code : {ticket_create_result_code}")
                    wb.change_cell_data(task_ws, task_row_index.index('key')+1, count, ticket_create_result_text)
                    logging.debug(ticket_create_result_text)
                elif ticket_create_result_code == 201:
                    key = ticket_result.json()["key"]
                    logging.info(key)
                    logging.debug(ticket_result.json())
                    loggas.input_message(path = message_path,message = f"create ticket {key} done!, status code : {ticket_create_result_code}")
                    wb.change_cell_data(task_ws, task_row_index.index('key')+1, count, key)
                    link_between_task_TQAOD(rh,task_excel_data['Link'],key)
                wb.save_workbook(file)
    wb.close_workbook()
    loggas.input_message(path = message_path,message = "task import done!")
    return 0

#======================= create logwork ===============================================
def find_logwork_info(list_opened_tasks,rh, summary,logwork_time):
    logwork_info = {
        "key":None,
        "logwork_id":None
    }
    #find task by summary
    if summary in list(list_opened_tasks.values()):
        key = list(list_opened_tasks.keys())[list(list_opened_tasks.values()).index(summary)]
        logwork_info['key'] = key
        logworks = rh.getworklogs(key)
        for logwork in logworks['worklogs']:
            if logwork_time in str(logwork):
                logwork_info['logwork_id'] = logwork['id']
    return logwork_info

def make_logwork(rh,data,index):
    username = rh.getusername()
    logwork_excel_data ={}
    mapping_data =configus.load_config(os.path.join('static','config','field_mapping.json'))
    logwork_field = mapping_data['logwork_field']
    for index_data in index:
        logwork_excel_data[str(index_data)] = str(data[index.index(index_data)].value)
        logwork_excel_data['author'] = {"name":username}
    try:
        logwork_excel_data['started'] = logwork_excel_data['date'][0:10]  + "T" + str(logwork_excel_data['start']) + ".000+0900"
        logwork_excel_data['timeSpentSeconds'] = str(int((datetime.datetime.strptime(logwork_excel_data['end'],'%H:%M:%S') - datetime.datetime.strptime(logwork_excel_data['start'], '%H:%M:%S')).total_seconds()))
    except:
        logwork_excel_data['summary'] = 'data type error'
    return logwork_excel_data

def importLogwork(rh, file):
    mapping_data =configus.load_config(os.path.join('static','config','field_mapping.json'))
    logwork_field = mapping_data['logwork_field']
    loggas.input_message(path = message_path,message = ' ========== update logwork========== ')
    loggas.input_message(path = message_path,message = 'start for logwork')
    wb = excelium.Workbook(file,read_only=False,data_only=False)
    #check logwork sheet validation
    if 'logwork' not in wb.get_sheet_list():
        loggas.input_message(path = message_path,message = "there is no logwork sheet.")
        loggas.input_message(path = message_path,message = "please check excel sheet.")
        return 0
    # ===========================make task in MakeTask sheet===============================
    logwork_ws = wb.get_worksheet('logwork')
    logwork_row_index = wb.get_first_row('logwork')
    list_opened_tasks = check_ticket_list_in_jira(rh)
    count = 0
    
    for data in logwork_ws.rows:
        count += 1  # must set correct key value in excel (index start at 1)
        logwork_excel_data ={}
        logwork_field = mapping_data['logwork_field']
        summary = data[logwork_row_index.index('summary')].value
        if summary is None:
            break
        if summary != 'summary':
            logwork_excel_data = make_logwork(rh,data,logwork_row_index)
            searched_logwork = find_logwork_info(list_opened_tasks,rh, logwork_excel_data['summary'],logwork_excel_data['started'])
            logwork_excel_data['key'] = searched_logwork['key']
            logwork_excel_data['id'] = searched_logwork['logwork_id']
            for field in logwork_field.keys():
                    logwork_field[field] = logwork_excel_data[field]
            logging.info(logwork_excel_data)
            logging.info(logwork_field)
            
            loggas.input_message(path = message_path,message = f"{logwork_excel_data['summary']}")
            if logwork_excel_data['key'] is None and logwork_excel_data['logwork_id'] is None:
                logging.info(f'there is no task {logwork_excel_data["summary"]}')
                loggas.input_message(path = message_path,message = 'no task please make task')
                loggas.input_message(path = message_path,message = f"{logwork_excel_data['summary']}")
                wb.change_cell_data(logwork_ws, logwork_row_index.index('key')+1, count, 'no_task')
                wb.change_cell_data(logwork_ws, logwork_row_index.index('id')+1, count, 'no_logwork')
            if logwork_excel_data['key'] is not None and logwork_excel_data['id'] is None:
                result = rh.submitlogwork(logwork_excel_data['key'], logwork_field)
                logging.debug(result.text)
                if result.status_code != 201:
                    loggas.input_message(path = message_path,message = 'there is a error, refer to the message in excel')
                    logging.info('error reasion : %s' %result.text)
                    wb.change_cell_data(logwork_ws, logwork_row_index.index('key')+1, count, logwork_excel_data['key'])
                    wb.change_cell_data(logwork_ws, logwork_row_index.index('id')+1, count, result.text)
                else:
                    #
                    loggas.input_message(path = message_path,message = 'logwork imported! key: %s and logwork id: %s' %(logwork_excel_data['key'],result.json()['id']))
                    wb.change_cell_data(logwork_ws, logwork_row_index.index('key')+1, count, logwork_excel_data['key'])
                    wb.change_cell_data(logwork_ws, logwork_row_index.index('id')+1, count, result.json()['id'])
            if logwork_excel_data['key'] is not None and logwork_excel_data['id'] is not None:
                logging.info('logwork already exists -%s / %s' % (logwork_excel_data['key'], logwork_excel_data['id']))
                loggas.input_message(path = message_path,message = 'logwork already exists -%s / %s\n' % (logwork_excel_data['key'], logwork_excel_data['id']))
                wb.change_cell_data(logwork_ws, logwork_row_index.index('key')+1, count, logwork_excel_data['key'])
                wb.change_cell_data(logwork_ws, logwork_row_index.index('id')+1, count, logwork_excel_data['id'])
    wb.save_workbook(file)
    wb.close_workbook()
    loggas.input_message(path = message_path,message = "logwork import done!")
    return 0


def importLogwork_old(rh, file):
    # init
    username = rh.getusername()
    config_data =configus.load_config(os.path.join('static','config','field_mapping.json'))
    loggas.input_message(path = message_path,message = ' ========== update logwork========== ')
    loggas.input_message(path = message_path,message = 'start for logwork')
    wb = excelium.Workbook(file,read_only=False,data_only=False)
    if 'logwork' in wb.get_sheet_list():
        # ===========================make task in MakeTask sheet===============================
        logwork_ws = wb.get_worksheet('logwork')
        logwork_row_index = wb.get_first_row('logwork')
        list_opened_tasks = check_ticket_list_in_jira(rh)
        count = 0
        for data in logwork_ws.rows:
            count += 1  # must set correct key value in excel (index start at 1)
            logwork_playloads = {}
            logwork_excel_data ={}
            #input value from excel to task_excel_data
            for row_data in logwork_row_index:
                logwork_excel_data[str(row_data)] = str(data[logwork_row_index.index(row_data)].value)
            def modify_logwork_excel():
                logwork_excel_data['logwork_start'] = logwork_excel_data['date'][0:10]  + "T" + str(logwork_excel_data['started']) + ".000+0900"
                logwork_excel_data['spent_second'] = str(int((datetime.datetime.strptime(logwork_excel_data['ended'],'%H:%M:%S') - datetime.datetime.strptime(logwork_excel_data['started'], '%H:%M:%S')).total_seconds()))
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
                logwork_playloads = jason.make_playload(logwork_excel_data,config_data['logwork_type_old'])['input_playload']
                loggas.input_message(path = message_path,message = f"{logwork_excel_data['summary']}")
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
                logging.info(logwork_excel_data)
                logwork_info = find_logwork_info(logwork_excel_data['summary'],logwork_excel_data['logwork_start'])
                logging.info(logwork_info)
                

                #input logwork
                if logwork_info['key'] == "no_task":
                    logging.info('there is no task %s' %logwork_excel_data['summary'])
                    loggas.input_message(path = message_path,message = 'no task please make task')
                    loggas.input_message(path = message_path,message = f"{logwork_excel_data['summary']}")
                    wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                    wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, logwork_info['logwork_id'])
                else:
                    if logwork_info['logwork_id'] != 'no_logwork':
                        logging.info('logwork already exists -%s / %s' % (logwork_info['key'], logwork_info['logwork_id']))
                        loggas.input_message(path = message_path,message = 'logwork already exists -%s / %s\n' % (logwork_info['key'], logwork_info['logwork_id']))
                        wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                        wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, logwork_info['logwork_id'])
                    else:
                        logging.info(logwork_playloads)
                        result = rh.submitlogwork(logwork_info['key'], logwork_playloads)
                        logging.info(result)
                        if result.status_code != 201:
                            loggas.input_message(path = message_path,message = 'there is a error, refer to the message in excel')
                            logging.info('error reasion : %s' %result.text)
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, result.text)
                        else:
                            #logging.debug(result.text)
                            loggas.input_message(path = message_path,message = 'logwork imported! key: %s and logwork id: %s' %(logwork_info['key'],result.json()['id']))
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('key'), count, logwork_info['key'])
                            wb.chagne_cell_data(logwork_ws, logwork_row_index.index('id'), count, result.json()['id'])
        loggas.input_message(path = message_path,message = "logwork import done!")
    else:
        loggas.input_message(path = message_path,message = "there is no logwork sheet.")
        loggas.input_message(path = message_path,message = "please check excel sheet.")
    return 0