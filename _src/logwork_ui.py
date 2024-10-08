#!/usr/bin/python
import os, sys
import threading


from PyQt5.QtWidgets import *
from PyQt5.QtCore import  Qt, pyqtSlot, QTimer, QTime
from PyQt5.QtGui import QTextCursor

from _src import logwork_import

refer_api = "local"
refer_api = "global"

if refer_api == "global":
    sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
    from _api import zyra, loggas, configus
if refer_api == "local":
    from _src._api import zyra, loggas, configus



logging = loggas.logger
logging_file_name = loggas.log_full_name


#set config

message_path = '_logs\output.txt'
config_path = os.path.join('static','config','config.json')
qss_path = os.path.join('static','css','style.qss')

config_data =configus.load_config(config_path)


logging.debug('qss_path is %s' %qss_path)
logging.debug('config_path is %s' %config_path)

class MyMainWindow(QMainWindow):
    def __init__(self,title):
        super().__init__()
        self.title = title
        self.setStyleSheet(open(qss_path, "r").read())
        self.initUI()
        self.show()

    def initUI(self):
        self.statusBar().showMessage('Ready')
        self.setWindowTitle(self.title)
        self.setGeometry(200, 200,600,600)
        self.setFixedSize(600,600)
        self.form_widget = FormWidget(self,self.statusBar())
        self.setCentralWidget(self.form_widget)


class FormWidget(QWidget):
    def __init__(self, parent, statusbar):
        super(FormWidget, self).__init__(parent)
        self.statusbar_status = 'not logged in'
        self.session = None
        self.session_info = None
        self.logging_temp = None
        self.file_path = None
        self.user = config_data['id']
        self.password = config_data['password']
        self.statusbar = statusbar
        self.initUI() 
        self.show()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.thread_ui)
        self.timer.start(1000)
        loggas.input_message(path = message_path,message = 'welcome to %s! :D' %self.user)
        loggas.input_message(path = message_path,message = 'current not login, start login')    

    def initUI(self):
        self.setStyleSheet(open(qss_path, "r").read())
        # make layout
        self.layout_main = QVBoxLayout(self)
        # login page layout
        self.layout_project = QHBoxLayout(self)
        self.login_layout = QHBoxLayout(self)
        self.log_layout = QHBoxLayout(self)
        
        #set user data
        self.login_layout_id_pw = QGridLayout(self)
        self.qlabel_id = QLabel('ID')
        self.qlabele_password = QLabel('Password')
        self.qlabel_id.setFixedWidth(100)
        self.qlabele_password.setFixedWidth(100)
        self.line_id = QLineEdit(self.user)
        self.line_password = QLineEdit(self.password)
        self.line_id.setFixedWidth(400)
        self.line_password.setFixedWidth(400)
        self.line_id.setAlignment(Qt.AlignLeft)
        self.line_password.setAlignment(Qt.AlignLeft)    
        self.line_password.setEchoMode(QLineEdit.Password)
        self.login_import_button = QPushButton('Log In')
        self.login_import_button.setFixedSize(60,60)
        self.login_layout_id_pw.addWidget(self.qlabel_id , 1, 0)
        self.login_layout_id_pw.addWidget(self.qlabele_password , 2, 0)
        self.login_layout_id_pw.addWidget(self.line_id, 1, 2)
        self.login_layout_id_pw.addWidget(self.line_password, 2, 2)
        self.login_layout.addLayout(self.login_layout_id_pw)
        self.login_layout.addWidget(self.login_import_button)
        
        # add log layout
        self.qtext_log_browser = QTextBrowser()
        self.qtext_log_browser.setReadOnly(1)
        self.log_layout.addWidget(self.qtext_log_browser)
        
        #add layout line
        self.layout_main.addLayout(self.layout_project)
        self.layout_main.addLayout(self.login_layout)
        self.layout_main.addLayout(self.log_layout)

        #events
        self.login_import_button.clicked.connect(self.on_start)
        self.line_password.returnPressed.connect(self.on_start)

    # add event list
    def open_fileName_dialog(self):
        set_dir = config_data['last_file_path']
        if set_dir == '':
            set_dir = os.path.join(os.path.expanduser('~'),'Desktop')
            loggas.input_message(path = message_path,message = 'folder path is %s' %set_dir)
        else:
            loggas.input_message(path = message_path,message = 'folder path is %s' %set_dir)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self,  "Open Logwork", set_dir, "Excel Files (*.xlsx)",options=options)
        if file_name == '':
            folder_path = set_dir
        else:
            folder_path = os.path.dirname(file_name)
        logging.debug('file path is %s' %file_name)
        logging.debug('folder path is %s' %folder_path)
        config_data['last_file_path']=folder_path
        #logging.debug(config_data)
        configus.save_config(config_data,config_path)
        return file_name

    def try_login(self):
        self.session = None
        self.session_info = None
        self.user = self.line_id.text()
        self.password = self.line_password.text()
        logging.info(f'user: {self.user} password: password')
        self.session, self.session_info, self.status_login = zyra.initsession(self.user, self.password, jira_url=config_data['jira_url'])
        #fail to login
        if self.status_login == False:
            loggas.input_message(path = message_path,message = "Login Fail")
            loggas.input_message(path = message_path,message = "please check your id and password or check internet connection")
            QMessageBox.about(self, "Login Fail", "please check your id and password or check internet connection")
        #if loggin success
        else:
            self.login_import_button.setText('Import\nLogwork')
            self.statusbar_status = 'logged in'
            
            #save config
            config_data['id'] = self.user
            config_data['password'] = self.password
            configus.save_config(config_data,config_path)
            loggas.input_message(path = message_path,message = 'login succeed, please start logwork import~!')

            #disable qtext and radiobutton
            self.line_id.setReadOnly(1)
            self.line_password.setReadOnly(1)
        return 0

    def create_tasks(self):
        self.login_import_button.setEnabled(False)
        if os.path.splitext(self.file_path)[1] == '.xlsx':
            self.rest_handler = zyra.Handler_Jira(self.session, jira_url=config_data['jira_url'])
            try:
                logwork_import.createTask(self.rest_handler, self.file_path,'makeTask')
            except ValueError:
                loggas.input_message(path = message_path,message = "wrong value input in your task sheet.")
                loggas.input_message(path = message_path,message = "please check your excel sheet.")
        self.login_import_button.setEnabled(True)
        return 0
    
    def import_logworks(self):
        self.login_import_button.setEnabled(False)
        self.rest_handler = zyra.Handler_Jira(self.session, jira_url=config_data['jira_url'])
        try:
            logwork_import.importLogwork(self.rest_handler, self.file_path)
        except ValueError:
            loggas.input_message(path = message_path,message = "wrong value input in your logwork sheet.")
            loggas.input_message(path = message_path,message = "please check your excel sheet.")
        self.login_import_button.setEnabled(True)
        return 0

    
    @pyqtSlot()
    def on_start(self):
        if self.statusbar_status == 'not logged in':
            self.try_login()    
        else:
            loggas.input_message(path = message_path,message = 'logged in')
            self.statusbar_status = 'logwork importing~'
            self.file_path = None
            self.file_path = self.open_fileName_dialog()
            if self.file_path is None:
                loggas.input_message(path = message_path,message = "plese select file")
            else:
                self.login_import_button.setEnabled(False)
                def task_logwork():    
                    self.create_tasks()
                    self.import_logworks()
                    self.statusbar_status = 'logwork import done.'
                thread_import = threading.Thread(target=task_logwork)
                thread_import.start()

    #set tread to change status bar and log browser
    def thread_ui(self):
        def show_time_statusbar():
            self.statusbar_time = QTime.currentTime().toString("hh:mm:ss")
            self.statusbar_message = self.statusbar_time + '\t-\t' + self.statusbar_status  
            self.statusbar.showMessage(str(self.statusbar_message))
          
        def show_logging():
            with open('_logs/output.txt', 'r') as myfile:
                self.output = myfile.read()
            if self.logging_temp == self.output:
                pass
            else:
                self.qtext_log_browser.setText(self.output)
                self.logging_temp = self.output
                self.qtext_log_browser.moveCursor(QTextCursor.End)
        show_time_statusbar()
        show_logging()
      

        
