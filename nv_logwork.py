import os, sys
from PyQt5.QtWidgets import QApplication

#add internal libary
from _src import logwork_ui, logwork_import

message_path = '_logs\output.txt'
config_path = os.path.join('static','config','config.json')
qss_path = os.path.join('static','css','style.qss')


refer_api = "local"
refer_api = "global"

if refer_api == "global":
    sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
    from _api import zyra, loggas, configus
if refer_api == "local":
    from _src._api import zyra, loggas,configus


logging= loggas.logger
logging_file_name = loggas.log_full_name

version = 'logwork v4.0'
revision_list=[
    '===============================================',
    'logwork v4.0',
    'Revision list',
    'v1.0 (2021-03-26) : initial release',
    'v1.1 (2021-04-08) : save last folder path which logwork excel opened.',
    'v1.2 (2021-04-14) : make tread to update status bar and logging browser and import',
    'v1.3 (2021-04-16) : add exception with logging',
    'v1.4 (2021-04-29) : add exception in case of no sheet.',
    'v2.0 (2021-05-04) : change structure excel and task, logwork (to sync config and excel file)',
    'v2.1 (2021-05-21) : bug fix to relative path',
    'v3.0 (2021-12-09) : serperate log(dev) and logging_message(user)',
    '                    sync new template (fot Map TQA and to synchronize between IT team DB and Excel)',
    '                    make link function',
    'v3.1 (2022-11-21) : save id and pw when logged in',
    'v4.0 (2023-01-31) : remove license function',
    '                    add custumcode - TASK_TYPE',
    'v5.0 (2024-08-27) : change function',
    '==============================================='
    ]


def debug_app():
    config_path = os.path.join('static','config','config.json')
    config_data =configus.load_config(config_path)
    lineEdit_user = config_data['id']
    lineEdit_password = config_data['password']
    session, session_info, status_login = zyra.initsession(lineEdit_user, lineEdit_password, jira_url=config_data['jira_url'])
    rest_handler=zyra.Handler_Jira(session,jira_url=config_data['jira_url'])
    file = r'D:\Tool\Logwork\logwork_v4.1_miskang.xlsx'
    #logwork_import.createTask(rest_handler, file,  sheet_name='makeTask')
    logwork_import.importLogwork(rest_handler, file)
    return 0

def start_app():
    loggas.remove_message(message_path)
    for revision in revision_list:
        loggas.input_message(path = message_path,message = revision,settime=False)
    app = QApplication(sys.argv)
    ex = logwork_ui.MyMainWindow(version)
    sys.exit(app.exec_())

if __name__ =='__main__':
    start_app()


