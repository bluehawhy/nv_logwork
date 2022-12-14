import os, sys
from PyQt5.QtWidgets import QApplication

from _src._api import logger, rest, logging_message
from _src import logwork_ui, license_key, logwork_import, logwork_refer

logging= logger.logger
logging_file_name = logger.log_full_name

version = 'logwork v3.1'
revision_list=[
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
    'v3.1 (2022-11-21) : save id and pw when logged in'    
    ]


def debug_app():
    lineEdit_user = 'miskang'
    lineEdit_password = '---'
    session = rest.initsession(lineEdit_user, lineEdit_password)
    rest_handler=rest.Handler_Jira(session[0])
    #folderpath = r'C:/Users/miskang/Desktop/'
    file = r'C:\Users\miskang\Downloads\logwork_v3.2_name.xlsx'
    logwork_import.createTask(rest_handler, file)
    logwork_import.importLogwork(rest_handler, file)

def start_app():
    message_path = logwork_refer.message_path
    logging_message.remove_message(message_path)
    logging_message.input_message(path = message_path,message = version)
    for revision in revision_list:
        logging_message.input_message(path = message_path,message = revision)
    app = QApplication(sys.argv)
    ex = logwork_ui.MyMainWindow(license_key.chekcLicense(),version)
    sys.exit(app.exec_())

if __name__ =='__main__':
    start_app()

