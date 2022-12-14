#!/usr/bin/python
import os
import sys
import time
import threading
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QGridLayout, QPlainTextEdit, QFileDialog, QMessageBox, QTextBrowser
from PyQt5.QtCore import pyqtSlot, QTimer, QTime

from PyQt5.QtGui import QTextCursor
from datetime import date


from _src._api import filepath, logger, rest, config, logging_message
from _src import logwork_import, license_key, logwork_refer

logging = logger.logger
logging_file_name = logger.log_full_name


#set config
message_path = logwork_refer.message_path
config_path = logwork_refer.config_path
qss_path = logwork_refer.qss_path
config_data =config.load_config(config_path)


logging.debug('qss_path is %s' %qss_path)
logging.debug('config_path is %s' %config_path)

class MyMainWindow(QMainWindow):
    def __init__(self, license,title):
        super().__init__()
        self.license = license
        self.title = title
        logging_message.input_message(path = message_path,message = 'license info: '+ str(self.license))
        self.today = date.today().strftime('%Y%m%d')
        self.valid_date = self.license['date']
        self.setStyleSheet(open(qss_path, "r").read())
        #==============================License check Line==============================
        #no license
        if self.license['user'] == 'empty':
            logging_message.input_message(path = message_path,message = 'there is no license')
            QMessageBox.about(self, "No license", "please input license! \npath:..\static\license")
            sys.exit()
        #license expired
        elif len(self.valid_date)!=8 or self.valid_date < self.today:
            logging_message.input_message(path = message_path,message = 'expired license. date is %s' %str(self.license['date']))
            QMessageBox.about(self, "License expired", "License expired!! \nplease input license! \npath:..\static\logwork\license")
            sys.exit()
        else:
            logging_message.input_message(path = message_path,message = 'license is valid.')
            self.initUI()
            self.show()

    def initUI(self):
        self.statusBar().showMessage('Ready')
        self.setWindowTitle(self.title)
        self.setGeometry(200, 200, 1200,600)
        #self.setFixedSize(600, 480)
        self.form_widget = FormWidget(self,self.license, self.statusBar())
        self.setCentralWidget(self.form_widget)


class FormWidget(QWidget):
    def __init__(self, parent, license, statusbar):
        super(FormWidget, self).__init__(parent)
        self.user = license['user']
        self.date = license['date']
        self.statusbar_status = 'not logged in'
        self.session_info = None
        self.logging_temp = None
        self.statusbar = statusbar
        self.initUI() 
        self.show()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.thread_ui)
        self.timer.start(1000)

    def initUI(self):
        self.setStyleSheet(open(qss_path, "r").read())
        # make layout
        self.layout_main = QVBoxLayout(self)
        # login page layout
        self.login_layout = QHBoxLayout(self)
        self.login_layout_id_pw = QGridLayout(self)
        #set user data
        self.user = config_data['id']
        self.password = config_data['password']
        self.line_id = QLineEdit(self.user)
        self.line_password = QLineEdit(self.password)
        
        if self.user == 'master':
            logging_message.input_message(path = message_path,message = 'welcome to master! :D')
            logging_message.input_message(path = message_path,message = 'current not login, start login')

        else:
            logging_message.input_message(path = message_path,message = 'welcome to %s! :D' %self.user)
            logging_message.input_message(path = message_path,message = 'current not login, start login')        
        self.line_password.setEchoMode(QLineEdit.Password)
        self.login_import_button = QPushButton('Log In')
        self.login_layout_id_pw.addWidget(QLabel('ID') , 1, 0)
        self.login_layout_id_pw.addWidget(QLabel('Password') , 2, 0)
        self.login_layout_id_pw.addWidget(self.line_id, 1, 2)
        self.login_layout_id_pw.addWidget(self.line_password, 2, 2)
        self.login_layout.addLayout(self.login_layout_id_pw)
        self.login_layout.addWidget(self.login_import_button)
        self.layout_main.addLayout(self.login_layout)

        # add log layout
        self.qtext_log_browser = QTextBrowser()
        self.qtext_log_browser.setReadOnly(1)
        self.layout_main.addWidget(self.qtext_log_browser)
        self.setLayout(self.layout_main)

        #login / import event
        self.login_import_button.clicked.connect(self.on_start)
        self.line_password.returnPressed.connect(self.on_start)


    # add event list
    def open_fileName_dialog(self):
        set_dir = config_data['last_file_path']
        if set_dir == '':
            set_dir = os.path.join(os.path.expanduser('~'),'Desktop')
            logging_message.input_message(path = message_path,message = 'folder path is %s' %set_dir)
        else:
            logging_message.input_message(path = message_path,message = 'folder path is %s' %set_dir)
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
        logging.debug(config_data)
        config.save_config(config_data,config_path)
        return file_name
    
    @pyqtSlot()
    def on_start(self):
        if self.statusbar_status == 'not logged in':
            self.user = self.line_id.text()
            self.password = self.line_password.text()
            logging.info('user: %s password: %s' %(self.user,'self.password'))
            self.session_list = rest.initsession(self.user, self.password)
            self.session = self.session_list[0]
            self.session_info = self.session_list[1]
            #fail to login
            if self.session_info == None:
                logging_message.input_message(path = message_path,message = "Login Fail")
                logging_message.input_message(path = message_path,message = "please check your id and password or check internet connection")
                QMessageBox.about(self, "Login Fail", "please check your id and password or check internet connection")
            #if loggin success
            else:
                self.login_import_button.setText('Import\nLogwork')
                self.statusbar_status = 'logged in'
                logging_message.input_message(path = message_path,message = 'login succeed, please start logwork import~!')
                config_data['id'] = self.user
                config_data['password'] = self.password
                config.save_config(config_data,config_path)
                self.line_id.setReadOnly(1)
                self.line_password.setReadOnly(1)
        else:
            logging_message.input_message(path = message_path,message = 'already logged in')
            self.statusbar_status = 'logwork importing~'
            self.file_path = ''
            self.file_path = self.open_fileName_dialog()
            if os.path.splitext(self.file_path)[1] == '.xlsx':
                self.rest_handler = rest.Handler_Jira(self.session)
                def import_logwork():
                    self.login_import_button.setEnabled(False)
                    try:
                        logwork_import.createTask(self.rest_handler, self.file_path)
                    except ValueError:
                        logging_message.input_message(path = message_path,message = "wrong value input in your task sheet.")
                        logging_message.input_message(path = message_path,message = "please check your excel sheet.")
                    try:
                        logwork_import.importLogwork(self.rest_handler, self.file_path)
                    except ValueError:
                        logging_message.input_message(path = message_path,message = "wrong value input in your logwork sheet.")
                        logging_message.input_message(path = message_path,message = "please check your excel sheet.")                    
                    finally:
                        self.login_import_button.setEnabled(True)
                        self.statusbar_status = 'logwork import done.'
                thread_import = threading.Thread(target=import_logwork)
                thread_import.start()
            else:
                logging_message.input_message(path = message_path,message = 'please input excel file~!')
                self.statusbar_status = 'logwork import fail.'

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
      

        
