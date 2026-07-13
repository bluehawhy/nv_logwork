# -*- coding: utf-8 -*-
#!/usr/bin/python

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QFileDialog, QMessageBox
    )
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor

import zyra, loggas, configus

logging = loggas.logger

# 경로 설정 (MESSAGE_PATH 제거)
CONFIG_PATH = Path('static/config/config.json')
QSS_PATH = Path('static/css/style.qss')

CONFIG_DATA = configus.load_config(str(CONFIG_PATH))


# -----------------------------------------------------------------------------
# Jira 백그라운드 작업을 안전하게 수행할 QThread 워커 정의
# -----------------------------------------------------------------------------
class JiraImportWorker(QThread):
    """메인 UI 스레드 풀림/잠김 및 진행 상황을 시그널로 안전하게 전달하는 워커"""
    finished = pyqtSignal(str)  # 작업 완료 시 상태 메시지 전달
    error_occurred = pyqtSignal(str)

    def __init__(self, session, file_path, jira_url):
        super().__init__()
        self.session = session
        self.file_path = file_path
        self.jira_url = jira_url

    def run(self):
        try:
            # Handler_Jira 초기화 및 태스크 생성
            rest_handler = zyra.Handler_Jira(self.session, jira_url=self.jira_url)
            
            # 1. Task 생성
            if Path(self.file_path).suffix == '.xlsx':
                try:
                    logwork_import.createTask(rest_handler, self.file_path, 'makeTask')
                except ValueError:
                    self.error_occurred.emit("wrong value input in your task sheet.\nPlease check your excel sheet.")
                    
            # 2. Logwork 이관
            try:
                logwork_import.importLogwork(rest_handler, self.file_path)
            except ValueError:
                self.error_occurred.emit("wrong value input in your logwork sheet.\nPlease check your excel sheet.")
                
            self.finished.emit('logwork import done.')
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
            self.finished.emit('Import failed due to error.')


# -----------------------------------------------------------------------------
# 메인 GUI 클래스들
# -----------------------------------------------------------------------------
class MyMainWindow(QMainWindow):
    def __init__(self, title):
        super().__init__()
        self.title = title
        
        # 안전한 QSS 로드
        if QSS_PATH.exists():
            with open(QSS_PATH, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
                
        self.initUI()
        self.show()

    def initUI(self):
        self.statusBar().showMessage('Ready')
        self.setWindowTitle(self.title)
        self.setGeometry(200, 200, 600, 600)
        self.setFixedSize(600, 600)
        
        self.form_widget = FormWidget(self, self.statusBar())
        self.setCentralWidget(self.form_widget)


class FormWidget(QWidget):
    def __init__(self, parent, statusbar):
        super().__init__(parent)
        self.statusbar = statusbar
        self.statusbar_status = 'not logged in'
        
        self.session = None
        self.session_info = None
        self.file_path = None
        
        self.user = CONFIG_DATA.get('id', '')
        self.password = CONFIG_DATA.get('password', '')
        
        self.initUI()
        
        # 1초 주기의 UI 타이머 (시계 업데이트)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui_state)
        self.timer.start(1000)
        
        # 초기 환영 메시지 출력
        self.write_log(f'welcome to {self.user}! :D')
        self.write_log('current not login, start login')

    def initUI(self):
        # 전체 메인 레이아웃
        layout_main = QVBoxLayout(self)
        
        # 내부 서브 레이아웃들
        layout_project = QHBoxLayout()
        login_layout = QHBoxLayout()
        log_layout = QHBoxLayout()
        login_layout_id_pw = QGridLayout()
        
        # ID / PW 입력 필드 세팅
        self.qlabel_id = QLabel('ID')
        self.qlabele_password = QLabel('Password')
        self.qlabel_id.setFixedWidth(100)
        self.qlabele_password.setFixedWidth(100)
        
        self.line_id = QLineEdit(self.user)
        self.line_password = QLineEdit(self.password)
        self.line_id.setFixedWidth(400)
        self.line_password.setFixedWidth(400)
        self.line_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_import_button = QPushButton('Log In')
        self.login_import_button.setFixedSize(70, 60)
        
        # 레이아웃 위젯 배치
        login_layout_id_pw.addWidget(self.qlabel_id, 1, 0)
        login_layout_id_pw.addWidget(self.qlabele_password, 2, 0)
        login_layout_id_pw.addWidget(self.line_id, 1, 2)
        login_layout_id_pw.addWidget(self.line_password, 2, 2)
        
        login_layout.addLayout(login_layout_id_pw)
        login_layout.addWidget(self.login_import_button)
        
        # 로그 브라우저 세팅
        self.qtext_log_browser = QTextBrowser()
        self.qtext_log_browser.setReadOnly(True)
        log_layout.addWidget(self.qtext_log_browser)
        
        # 메인 레이아웃에 배치
        layout_main.addLayout(layout_project)
        layout_main.addLayout(login_layout)
        layout_main.addLayout(log_layout)
        
        # 이벤트 시그널 연결
        self.login_import_button.clicked.connect(self.on_handle_action)
        self.line_password.returnPressed.connect(self.on_handle_action)

    def write_log(self, text):
        """텍스트 브라우저에 로그를 바로 출력하고 스크롤을 맨 아래로 내립니다."""
        self.qtext_log_browser.append(text)
        self.qtext_log_browser.moveCursor(QTextCursor.MoveOperation.End)

    def open_filename_dialog(self):
        """파일 탐색기를 열어 엑셀 경로를 획득하고 환경 설정을 업데이트합니다."""
        set_dir = CONFIG_DATA.get('last_file_path', '')
        if not set_dir:
            set_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
            
        self.write_log(f'folder path is {set_dir}')
        
        options = QFileDialog.Option()
        options |= QFileDialog.Option.DontUseNativeDialog
        
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Logwork", set_dir, "Excel Files (*.xlsx)", options=options
        )
        
        if file_name:
            folder_path = os.path.dirname(file_name)
            logging.debug(f'file path is {file_name}')
            logging.debug(f'folder path is {folder_path}')
            
            CONFIG_DATA['last_file_path'] = folder_path
            configus.save_config(CONFIG_DATA, str(CONFIG_PATH))
            return file_name
        return None

    def try_login(self):
        """Jira 서버 로그인을 시도합니다."""
        self.user = self.line_id.text()
        self.password = self.line_password.text()
        
        logging.info(f'Attempting login for user: {self.user}')
        self.session, self.session_info, status_login = zyra.initsession(
            self.user, self.password, jira_url=CONFIG_DATA.get('jira_url', '')
        )
        
        if not status_login:
            self.write_log("Login Fail")
            self.write_log("please check your credentials or network.")
            QMessageBox.critical(self, "Login Fail", "Please check your ID/Password or internet connection.")
        else:
            self.login_import_button.setText('Import\nLogwork')
            self.statusbar_status = 'logged in'
            
            CONFIG_DATA['id'] = self.user
            CONFIG_DATA['password'] = self.password
            configus.save_config(CONFIG_DATA, str(CONFIG_PATH))
            self.write_log('login succeed, please start logwork import~!')
            
            # 입력 창 잠금 및 비활성화 스타일시트 시각화
            self.line_id.setReadOnly(True)
            self.line_password.setReadOnly(True)
            self.line_id.setStyleSheet("color: gray; background-color: #f0f0f0;")
            self.line_password.setStyleSheet("color: gray; background-color: #f0f0f0;")

    @pyqtSlot()
    def on_handle_action(self):
        """로그인 혹은 파일 임포트 액션을 통합 제어하는 메인 라우터"""
        if self.statusbar_status == 'not logged in':
            self.try_login()
        else:
            self.write_log('logged in')
            self.file_path = self.open_filename_dialog()
            
            if not self.file_path:
                self.write_log("please select file")
                return

            # UI 버튼 비활성화 (스레드 세이프 시작점)
            self.login_import_button.setEnabled(False)
            self.statusbar_status = 'logwork importing~'
            
            # QThread를 이용한 백그라운드 워커 생성 및 시그널 바인딩
            self.worker = JiraImportWorker(self.session, self.file_path, CONFIG_DATA.get('jira_url', ''))
            self.worker.finished.connect(self.on_import_finished)
            self.worker.error_occurred.connect(self.on_import_error)
            self.worker.start()

    @pyqtSlot(str)
    def on_import_finished(self, final_status):
        """백그라운드 스레드가 완전히 완료되었을 때 메인 UI가 수신하는 슬롯"""
        self.statusbar_status = final_status
        self.write_log(final_status)
        self.login_import_button.setEnabled(True)

    @pyqtSlot(str)
    def on_import_error(self, error_msg):
        """백그라운드 스레드에서 도중에 ValueError 등 에러 메시지가 감지되었을 때 UI 노출"""
        self.write_log(error_msg)

    def update_ui_state(self):
        """1초 주기로 상태바의 시계 표기를 처리"""
        current_time = QTime.currentTime().toString("hh:mm:ss")
        self.statusbar.showMessage(f"{current_time}\t-\t{self.statusbar_status}")