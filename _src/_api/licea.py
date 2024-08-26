# -*- encoding: utf-8 -*-

import os, sys
import datetime
from PyQt5.QtWidgets import *

from . import configus, zyra


config_path ='static\config\config.json'
config_data =configus.load_config(config_path)
message_path = config_data['message_path']
qss_path  = config_data['qss_path']


SHIFT = 27
private_key = 'He was an old man who fished alone in a skiff in the Gulf Stream and he had gone eighty-four days now without taking a fish. In the first forty days a boy had been with him. But after forty days without a fish the boy’s parents had told him that the old man was now definitely and finally salao, which is the worst form of unlucky, and the boy had gone at their orders in another boat which caught three good fish the first week. It made the boy sad to see the old man come in each day with his skiff empty and he always went down to help him carry either the coiled lines or the gaff and harpoon and the sail that was furled around the mast. The sail was patched with flour sacks and, furled, it looked like the flag of permanent defeat.'

def encrypt(raw):
    ret = ''
    raw = raw+private_key
    for char in raw:
        ret += chr(ord(char) + SHIFT)
    return ret

def decrypt(raw):
    ret = ''
    for char in raw:
        ret += chr(ord(char) - SHIFT)
    ret = ret.replace(private_key,'')
    return ret

def createLicense(raw):
    os.makedirs('static/license') if not os.path.isdir('static/license') else None
    f = open("static/license/license.txt", 'w', encoding="utf-8")
    encrypted = encrypt(raw)
    f.write(encrypted)
    f.close()

def check_License():
    license = {'user': 'user', 'date': '19000101'}
    license_path = os.path.join(os.path.dirname(sys.argv[0]),'static','license','license.txt')
    if os.path.exists(license_path):
        f = open(license_path, 'r', encoding="utf-8")
        line = f.readline()
        f.close()
        decryptd= decrypt(line)
        license['user'] = decryptd.split('_')[0]
        license['date'] = decryptd.split('_')[1]
    return license

def valild_License(license):
    day_validation = False
    license_str = license['date']
    today_str = datetime.date.today().strftime("%Y%m%d")
    if license_str >= today_str:
            day_validation = True
    return day_validation

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(open(qss_path, "r").read())
        self.initUI()
        self.show()
        msg = QMessageBox()
        msg.setWindowTitle('Login - update license')
        msg.setGeometry(300,300,400,200)
        msg.setText('license is invaild so please login again')
        msg.exec_()

    def initUI(self):
        self.statusBar().showMessage('')
        self.setWindowTitle('Login - update license')
        self.setGeometry(300,300,400,200)
        #self.setFixedSize(600, 480)
        self.LoginForm = LoginForm(self)
        self.setCentralWidget(self.LoginForm)

class LoginForm(QWidget):
    def __init__(self, parent):
        super(LoginForm, self).__init__(parent)
        layout = QGridLayout()
        
        user = config_data['id']
        label_name = QLabel('Username')
        self.line_id = QLineEdit(user)
        self.line_id.setPlaceholderText('Please enter your username')
        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.line_id, 0, 1)

        password = config_data['password'] 
        label_password = QLabel('Password')
        self.line_password = QLineEdit(password)
        self.line_password.setPlaceholderText('Please enter your password')
        self.line_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.line_password, 1, 1)

        self.button_login = QPushButton('Login')
        self.button_login.clicked.connect(self.make_license)
        layout.addWidget(self.button_login, 2, 0, 1, 2)
        layout.setRowMinimumHeight(2, 75)

        self.setLayout(layout)

    def make_license(self):
        msg = QMessageBox()
        self.user = self.line_id.text()
        self.password = self.line_password.text()
        self.session,self.session_info, self.status_login = zyra.initsession(username = self.user, password= self.password)
        #fail to login
        if self.status_login is False:
            QMessageBox.about(self, "Login Fail", "please check your password or internet connection")
        #if loggin success
        else:
            QMessageBox.about(self, "Login success", "please close the window and restart again")
            config_data['id'] = self.user
            config_data['password'] = self.password
            configus.save_config(config_data,config_path)
            self.line_id.setReadOnly(1)
            self.line_password.setReadOnly(1)
            self.button_login.setEnabled(False)
            #create license
            license_for_day_100 = datetime.date.today() + datetime.timedelta(days=100)
            licen_raw = self.user+"_"+ license_for_day_100.strftime("%Y%m%d")
            createLicense(licen_raw)
        return 0
  
