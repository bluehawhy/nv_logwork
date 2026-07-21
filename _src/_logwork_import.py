# -*- coding: utf-8 -*-
#!/usr/bin/python

import ast
import datetime
from pathlib import Path
from . import loggas, excelium, configus

# 로거 및 기본 경로 설정 (Pathlib 활용으로 OS 간 호환성 확보)
logging = loggas.logger
MESSAGE_PATH = Path('_logs/output.txt')
CONFIG_PATH = Path('static/config/config.json')
QSS_PATH = Path('static/css/style.qss')

CONFIG_DATA = configus.load_config(str(CONFIG_PATH))

# -----------------------------------------------------------------------------
# 2. 공통 유틸리티 함수
# -----------------------------------------------------------------------------
def check_ticket_list_in_jira(rh):
    """Jira에서 현재 사용자가 보고자이고 해결되지 않은 TQA_OD 프로젝트 티켓 목록을 가져옵니다."""
    logging.info('Get task list from Jira')
    query = 'project = TQA_OD and reporter = currentUser() and status not in (Resolved, Closed, Cancelled)'
    issues = rh.searchIssueByQuery(query)
    
    return {issue: issues[issue]['summary'] for issue in issues}

def make_dict_from_string(string_data):
    """문자열 리터럴을 딕셔너리나 리스트 객체로 변환합니다."""
    try:
        converted = ast.literal_eval(string_data)
        if isinstance(converted, (dict, list)):
            return converted
        return string_data
    except (SyntaxError, ValueError):
        return string_data

# -----------------------------------------------------------------------------
# 3. 티켓 생성 관련 함수
# -----------------------------------------------------------------------------
def link_between_task_tqa_od(rh, key1, key2):
    """두 티켓 간에 링크를 생성합니다."""
    link_id = '10900'
    if str(key1).strip() in ('None', '__', '0', '-'):
        loggas.input_message(path=MESSAGE_PATH, message=f"Key is wrong. Key name: {key1}")
        return 0

    result = rh.createLinked(key1, key2, link_id)
    msg = f"Ticket Link done! Status: {result.status_code} | Main: {key1} -> Linked: {key2}"
    logging.info(msg)
    loggas.input_message(path=MESSAGE_PATH, message=msg)
    return 0

def modify_data(excel_data, task_row_index):
    """엑셀 행 데이터를 Jira 포맷에 맞게 변환 및 가공합니다."""
    task_excel_data = {str(row): str(excel_data[task_row_index.index(row)].value) for row in task_row_index}
    task_excel_data['assignee'] = CONFIG_DATA.get('id', '')

    try:
        # 시간 단위 변환 (일 -> 분) 및 날짜 포맷팅
        task_excel_data['originalestimate'] = f"{float(task_excel_data['originalestimate']) * 480:.0f}m"
        task_excel_data['duedate'] = f"{task_excel_data['duedate'][:10]}T18:00:00.000+0900"
        task_excel_data['plannedstart'] = f"{task_excel_data['plannedstart'][:10]}T09:00:00.000+0900"
        task_excel_data['plannedend'] = f"{task_excel_data['plannedend'][:10]}T18:00:00.000+0900"
    except (ValueError, TypeError, KeyError):
        # 엑셀 데이터 포맷이 잘못되었을 경우 기본값 적용
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        task_excel_data['originalestimate'] = "300m"
        task_excel_data['duedate'] = f"{today_str}T18:00:00.000+0900"
        task_excel_data['plannedstart'] = f"{today_str}T09:00:00.000+0900"
        task_excel_data['plannedend'] = f"{today_str}T18:00:00.000+0900"
        
    return task_excel_data

def mapping_data(task_excel_data):
    """필드 매핑 설정을 기반으로 Jira 텍스트 데이터를 구성합니다."""
    ticket_import_data = {"fields": {}}
    mapping_path = Path('static/config/field_mapping.json')
    mapping_config = configus.load_config(str(mapping_path))
    
    task_field = mapping_config['task_field']
    task_field_mapping = mapping_config['task_field_mapping']

    for field_key, mapping_key in task_field_mapping.items():
        if mapping_key in task_excel_data:
            excel_value = task_excel_data[mapping_key]
            if excel_value != '0' and field_key in task_field:
                replace_value = str(task_field[field_key]).replace('-', excel_value)
                ticket_import_data["fields"][field_key] = make_dict_from_string(replace_value)
                
    return ticket_import_data

def create_task(rh, file_path, sheet_name='SW_TQA_makeTask'):
    """엑셀 파일을 읽어 Jira 티켓을 대량 생성하거나 기존 티켓과 링크를 보완합니다."""
    list_opened_tasks = check_ticket_list_in_jira(rh)
    # 검색 편의를 위해 {summary: key} 형태의 역방향 딕셔너리 생성
    summary_to_key = {v: k for k, v in list_opened_tasks.items()}

    loggas.input_message(path=MESSAGE_PATH, message='========== Create Task ==========')
    logging.debug('Reading excel sheet...')
    
    wb = excelium.Workbook(file_path, read_only=False, data_only=False)
    if sheet_name not in wb.get_sheet_list():
        loggas.input_message(path=MESSAGE_PATH, message="There is no maketask sheet. Please check excel.")
        return 0
    
    task_ws = wb.get_worksheet(sheet_name)
    task_row_index = wb.get_first_row(sheet_name)
    summary_idx = task_row_index.index('summary')
    key_idx = task_row_index.index('key') + 1

    for count, data in enumerate(task_ws.rows, start=1):
        summary = data[summary_idx].value
        if summary is None:
            break
        if summary == 'summary':
            continue

        task_excel_data = modify_data(data, task_row_index)
        ticket_import_data = mapping_data(task_excel_data)
        logging.info(ticket_import_data)

        # 1) 이미 존재하는 티켓인 경우 -> 스킵 및 링크 처리
        if task_excel_data['summary'] in summary_to_key:
            existing_key = summary_to_key[task_excel_data['summary']]
            loggas.input_message(path=MESSAGE_PATH, message=f"Task exists {existing_key} -> Skip")
            logging.info(f"Task exists. Key: {existing_key}, Summary: {task_excel_data['summary']}")
            wb.change_cell_data(task_ws, key_idx, count, existing_key)
            link_between_task_tqa_od(rh, task_excel_data['Link'], existing_key)
            
        # 2) 신규 티켓 생성
        else:
            loggas.input_message(path=MESSAGE_PATH, message=f"Make task - {task_excel_data['summary']}")
            ticket_result = rh.createTicket(ticket_import_data)
            status_code = ticket_result.status_code
            
            if status_code == 201:
                new_key = ticket_result.json()["key"]
                logging.info(f"Created key: {new_key}")
                loggas.input_message(path=MESSAGE_PATH, message=f"Create ticket {new_key} done! (Status: {status_code})")
                wb.change_cell_data(task_ws, key_idx, count, new_key)
                link_between_task_tqa_od(rh, task_excel_data['Link'], new_key)
            else:
                loggas.input_message(path=MESSAGE_PATH, message=f"Can't make ticket. Status code: {status_code}")
                wb.change_cell_data(task_ws, key_idx, count, ticket_result.text)
                logging.info(ticket_result.text)
                
        wb.save_workbook(file_path)
        
    wb.close_workbook()
    loggas.input_message(path=MESSAGE_PATH, message="Task import done!")
    return 0

# -----------------------------------------------------------------------------
# 4. 작업 로그(Logwork) 관련 함수
# -----------------------------------------------------------------------------
def find_logwork_info(list_opened_tasks, rh, summary, logwork_time):
    """동일한 요약(Summary)과 시작 시간을 가진 기존 작업 로그 정보를 찾습니다."""
    logwork_info = {"key": None, "logwork_id": None}
    
    # 역방향 딕셔너리로 Key 추출
    summary_to_key = {v: k for k, v in list_opened_tasks.items()}
    if summary in summary_to_key:
        key = summary_to_key[summary]
        logwork_info['key'] = key
        logworks = rh.getworklogs(key)
        
        for logwork in logworks.get('worklogs', []):
            if logwork_time in str(logwork):
                logwork_info['logwork_id'] = logwork['id']
                break
                
    return logwork_info

def make_logwork(rh, data, index):
    """엑셀 행 데이터를 바탕으로 Jira 작업 로그 구조를 생성합니다."""
    username = rh.getusername()
    logwork_excel_data = {str(idx): str(data[index.index(idx)].value) for idx in index}
    logwork_excel_data['author'] = {"name": username}
    
    try:
        logwork_excel_data['started'] = f"{logwork_excel_data['date'][:10]}T{logwork_excel_data['start']}.000+0900"
        time_format = '%H:%M:%S'
        duration = datetime.datetime.strptime(logwork_excel_data['end'], time_format) - datetime.datetime.strptime(logwork_excel_data['start'], time_format)
        logwork_excel_data['timeSpentSeconds'] = str(int(duration.total_seconds()))
    except (ValueError, TypeError, KeyError):
        logwork_excel_data['summary'] = 'data type error'
        
    return logwork_excel_data

def import_logwork(rh, file_path):
    """엑셀의 logwork 시트를 읽어 Jira에 작업 로그를 업로드합니다."""
    mapping_path = Path('static/config/field_mapping.json')
    mapping_config = configus.load_config(str(mapping_path))
    logwork_field_template = mapping_config['logwork_field']

    loggas.input_message(path=MESSAGE_PATH, message=' ========== Update Logwork ========== ')
    loggas.input_message(path=MESSAGE_PATH, message='Start for logwork')
    
    wb = excelium.Workbook(file_path, read_only=False, data_only=False)
    if 'logwork' not in wb.get_sheet_list():
        loggas.input_message(path=MESSAGE_PATH, message="There is no logwork sheet. Please check excel.")
        return 0

    logwork_ws = wb.get_worksheet('logwork')
    logwork_row_index = wb.get_first_row('logwork')
    list_opened_tasks = check_ticket_list_in_jira(rh)
    
    summary_idx = logwork_row_index.index('summary')
    key_idx = logwork_row_index.index('key') + 1
    id_idx = logwork_row_index.index('id') + 1

    for count, data in enumerate(logwork_ws.rows, start=1):
        summary = data[summary_idx].value
        if summary is None:
            break
        if summary == 'summary':
            continue

        logwork_excel_data = make_logwork(rh, data, logwork_row_index)
        searched_logwork = find_logwork_info(list_opened_tasks, rh, logwork_excel_data['summary'], logwork_excel_data['started'])
        
        logwork_excel_data['key'] = searched_logwork['key']
        logwork_excel_data['id'] = searched_logwork['logwork_id']

        # 템플릿 필드 복사 및 값 업데이트
        logwork_field = logwork_field_template.copy()
        for field in logwork_field.keys():
            if field in logwork_excel_data:
                logwork_field[field] = logwork_excel_data[field]

        logging.info(logwork_excel_data)
        loggas.input_message(path=MESSAGE_PATH, message=f"{logwork_excel_data['summary']}")

        # Case 1: 연결된 티켓 자체가 없는 경우
        if logwork_excel_data['key'] is None:
            logging.info(f"There is no task: {logwork_excel_data['summary']}")
            loggas.input_message(path=MESSAGE_PATH, message='No task, please create task first.')
            wb.change_cell_data(logwork_ws, key_idx, count, 'no_task')
            wb.change_cell_data(logwork_ws, id_idx, count, 'no_logwork')
            
        # Case 2: 티켓은 있으나 로그가 등록되지 않은 경우 -> 등록 진행
        elif logwork_excel_data['id'] is None:
            result = rh.submitlogwork(logwork_excel_data['key'], logwork_field)
            logging.debug(result.text)
            
            if result.status_code != 201:
                loggas.input_message(path=MESSAGE_PATH, message='Error occurred, check the message in excel.')
                logging.info(f"Error reason: {result.text}")
                wb.change_cell_data(logwork_ws, key_idx, count, logwork_excel_data['key'])
                wb.change_cell_data(logwork_ws, id_idx, count, result.text)
            else:
                new_log_id = result.json().get('id', 'unknown')
                loggas.input_message(path=MESSAGE_PATH, message=f"Logwork imported! Key: {logwork_excel_data['key']} | ID: {new_log_id}")
                wb.change_cell_data(logwork_ws, key_idx, count, logwork_excel_data['key'])
                wb.change_cell_data(logwork_ws, id_idx, count, new_log_id)
                
        # Case 3: 이미 로그가 존재하는 경우 -> 스킵
        else:
            msg = f"Logwork already exists - {logwork_excel_data['key']} / {logwork_excel_data['id']}"
            logging.info(msg)
            loggas.input_message(path=MESSAGE_PATH, message=msg + "\n")
            wb.change_cell_data(logwork_ws, key_idx, count, logwork_excel_data['key'])
            wb.change_cell_data(logwork_ws, id_idx, count, logwork_excel_data['id'])

        wb.save_workbook(file_path)

    wb.close_workbook()
    loggas.input_message(path=MESSAGE_PATH, message="Logwork import done!")
    return 0