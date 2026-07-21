import os
import sys
from PyQt6.QtWidgets import QApplication

#add internal libary
from _src import _logwork_ui, zyra, loggas, configus


config_path = os.path.join('static','config','config.json')
qss_path = os.path.join('static','css','style.qss')

logging= loggas.logger

version = 'logwork v5.0'

def debug_app():
    """Function printing python version."""
    config_path = os.path.join('static','config','config.json')
    config_data =configus.load_config(config_path)
    lineEdit_user = config_data['id']
    lineEdit_password = config_data['password']
    session, session_info, status_login = zyra.initsession(lineEdit_user, lineEdit_password, jira_url=config_data['jira_url'])
    return 0

def start_app():
    app = QApplication(sys.argv)
    window = _logwork_ui.MainWindow(version)
    window.show()
    sys.exit(app.exec())

if __name__ =='__main__':
    loggas.set_debug_logging(True)
    start_app()
