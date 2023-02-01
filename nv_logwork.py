import os, sys
from PyQt5.QtWidgets import QApplication

from _src._api import logger, logging_message, jira_rest
from _src import logwork_ui, logwork_import, logwork_refer


logging= logger.logger
logging_file_name = logger.log_full_name

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
    '==============================================='
    ]


def debug_app():
    lineEdit_user = '---'
    lineEdit_password = '--1'
    session,session_info = jira_rest.initsession(lineEdit_user, lineEdit_password)
    rest_handler=jira_rest.Handler_Jira(session)
    #folderpath = r'C:/Users/miskang/Desktop/'
    file = r'D:\Tool\Logwork\logwork_v3.7_miskang.xlsx'
    logwork_import.createTask(rest_handler, file)
    #logwork_import.importLogwork(rest_handler, file)

def start_app():
    message_path = logwork_refer.message_path
    logging_message.remove_message(message_path)
    for revision in revision_list:
        logging_message.input_message(path = message_path,message = revision,settime=False)
    app = QApplication(sys.argv)
    ex = logwork_ui.MyMainWindow(version)
    sys.exit(app.exec_())

if __name__ =='__main__':
    start_app()


