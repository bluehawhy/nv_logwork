# -*- coding: utf-8 -*-
#!/usr/bin/python

import os
import sys
import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextBrowser, QFileDialog, QMessageBox,
    QDateEdit, QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView, QDialog
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QTime, QDate, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QTextCursor, QFont

# 사용자 정의 모듈 임포트 유지
from . import zyra, loggas, configus, _logwork_import
logging = loggas.logger

# 경로 설정
CONFIG_PATH = Path('static/config/config.json')
QSS_PATH = Path('static/css/style.qss')
CONFIG_DATA = configus.load_config(str(CONFIG_PATH))

# 스타일시트 로드 함수
def load_stylesheet(widget, file_path=QSS_PATH):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                style_data = f.read()
                widget.setStyleSheet(style_data)
        else:
            print(f"Style file not found: {file_path}")
    except Exception as e:
        print(f"Error loading style: {e}")


# -----------------------------------------------------------------------------
# README.md에서 Revision List를 분리/파싱하는 헬퍼 함수
# -----------------------------------------------------------------------------
def get_revision_list():
    """
    README.md 파일을 찾아서 'Revision list' 단락 아래의 이력들을 파싱해 반환합니다.
    파일이 없거나 읽지 못할 경우 기본 하드코딩된 리스트를 반환합니다.
    """
    fallback_revisions = None

    # README.md 탐색 경로 후보들
    candidates = [
        Path('README.md'),
        Path('../README.md'),
        Path(__file__).resolve().parents[1] / 'README.md',
        Path(__file__).resolve().parents[2] / 'README.md'
    ]

    readme_path = None
    for path in candidates:
        if path.exists():
            readme_path = path
            break

    if not readme_path:
        return fallback_revisions

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        revisions = []
        is_revision_section = False
        
        for line in lines:
            clean_line = line.strip()
            # Revision list 시작 지점 감지
            if 'Revision list' in clean_line or 'Revision List' in clean_line:
                is_revision_section = True
                continue
            
            if is_revision_section:
                # 다음 대제목(#)이나 비어있지 않은 다른 세션이 크게 시작되면 종료
                if clean_line.startswith('#') and not ('v' in clean_line and '.' in clean_line):
                    break
                
                # 내용 수집 (버전 형식 'vX.X'을 포함하고 있거나 들여쓰기된 로그 기록인 경우)
                if clean_line:
                    # 마크다운의 bullet point(-, *, ') 기호 정리
                    for prefix in ['-', '*', "'", '"']:
                        if clean_line.startswith(prefix):
                            clean_line = clean_line.lstrip(prefix).strip()
                    if clean_line.endswith("'") or clean_line.endswith('"'):
                        clean_line = clean_line[:-1].strip()
                    
                    if clean_line:
                        revisions.append(clean_line)
                        
        if revisions:
            return revisions
    except Exception as e:
        print(f"Error reading README.md: {e}")
        
    return fallback_revisions


# -----------------------------------------------------------------------------
# Revision List 전용 모달 팝업 창 클래스
# -----------------------------------------------------------------------------
class RevisionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Revision History")
        self.resize(500, 380)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 타이틀 레이블
        title = QLabel("System Revision History")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # 이력 출력용 텍스트 브라우저
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                line-height: 140%;
            }
        """)
        
        # 동적 파일 파싱 결과 바인딩
        revisions = get_revision_list()
        self.text_browser.append("\n".join(revisions))
        layout.addWidget(self.text_browser)

        # 닫기 버튼
        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(30)
        btn_close.setFixedWidth(80)
        btn_close.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)


# -----------------------------------------------------------------------------
# Jira 백그라운드 작업 QThread 워커
# -----------------------------------------------------------------------------
class JiraImportWorker(QThread):
    finished = pyqtSignal(str)  
    error_occurred = pyqtSignal(str)

    def __init__(self, session, file_path, jira_url):
        super().__init__()
        self.session = session
        self.file_path = file_path
        self.jira_url = jira_url

    def run(self):
        try:
            rest_handler = zyra.Handler_Jira(self.session, jira_url=self.jira_url)
            
            if Path(self.file_path).suffix == '.xlsx':
                try:
                    _logwork_import.create_task(rest_handler, self.file_path, 'makeTask')
                except ValueError:
                    self.error_occurred.emit("wrong value input in your task sheet.\nPlease check your excel sheet.")
                    
            try:
                _logwork_import.import_logwork(rest_handler, self.file_path)
            except ValueError:
                self.error_occurred.emit("wrong value input in your logwork sheet.\nPlease check your excel sheet.")
                
            self.finished.emit('logwork import done.')
        except Exception as e:
            logging.info(f"Unexpected error: {str(e)}")
            self.finished.emit('Import failed due to error.')


# -----------------------------------------------------------------------------
# 메인 윈도우 프레임 클래스 (컨트롤 타워)
# -----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, title="Jira Logwork System"):
        super().__init__()
        self.title = title
        self.statusbar_status = 'not logged in'
        self.drag_pos = None
        self.resize_edge = "none"
        self.MARGIN = 10  

        self.selected_task_id = None # [추가] 선택된 Task ID를 전역적으로 추적하기 위한 변수

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.initUI()
        load_stylesheet(self)

    def initUI(self):
        self.setMinimumSize(350, 250)
        self.resize(350, 250)

        self.central_widget = QWidget()
        self.central_widget.setObjectName("mainWidget")
        self.central_widget.setMouseTracking(True)
        self.setCentralWidget(self.central_widget)

        self.master_layout = QVBoxLayout(self.central_widget)
        self.master_layout.setContentsMargins(0, 0, 0, 0)
        self.master_layout.setSpacing(0)

        self.create_title_bar()

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(15, 10, 15, 15)
        self.master_layout.addWidget(self.content_area)

        self.show_login_view()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_statusbar_clock)
        self.timer.start(1000)

    def create_title_bar(self):
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(35)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 0, 0)
        title_layout.setSpacing(0)

        self.title_label = QLabel(f"{self.title} - {self.statusbar_status}")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setProperty("class", "sectionLabel")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        # R (Revision) 버튼 추가 (디자인 통일성을 위해 titleBtn 클래스 공유)
        self.rev_btn = QPushButton("R")
        self.rev_btn.setObjectName("revBtn")
        self.rev_btn.setProperty("class", "titleBtn")
        self.rev_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rev_btn.clicked.connect(self.show_revision_dialog)

        self.min_btn = QPushButton("ㅡ")
        self.min_btn.setProperty("class", "titleBtn")
        self.min_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.min_btn.clicked.connect(self.showMinimized)

        self.max_btn = QPushButton("□")
        self.max_btn.setProperty("class", "titleBtn")
        self.max_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.max_btn.clicked.connect(self.toggle_maximize)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setProperty("class", "titleBtn")
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.clicked.connect(self.close)

        title_layout.addWidget(self.rev_btn)  # 축소 아이콘 왼쪽에 R 버튼 배치
        title_layout.addWidget(self.min_btn)
        title_layout.addWidget(self.max_btn)
        title_layout.addWidget(self.close_btn)
        
        self.master_layout.addWidget(title_bar)

    @pyqtSlot()
    def show_revision_dialog(self):
        """ R 버튼 클릭 시 모달 다이얼로그 실행 """
        dialog = RevisionDialog(self)
        dialog.exec()

    def show_login_view(self):
        self.clear_content_area()
        
        self.login_container = QWidget()
        login_layout = QVBoxLayout(self.login_container)
        login_layout.setContentsMargins(10, 10, 10, 10)
        login_layout.setSpacing(10)

        id_layout = QHBoxLayout()
        self.label_id = QLabel('ID')
        self.label_id.setFixedWidth(65)
        self.line_id = QLineEdit(CONFIG_DATA.get('id', ''))
        self.line_id.setFixedHeight(28)
        id_layout.addWidget(self.label_id)
        id_layout.addWidget(self.line_id)

        pw_layout = QHBoxLayout()
        self.label_password = QLabel('Password')
        self.label_password.setFixedWidth(65)
        self.line_password = QLineEdit(CONFIG_DATA.get('password', ''))
        self.line_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.line_password.setFixedHeight(28)
        pw_layout.addWidget(self.label_password)
        pw_layout.addWidget(self.line_password)

        self.login_button = QPushButton('Log In')
        self.login_button.setFixedHeight(35)
        self.login_button.clicked.connect(self.try_login)
        self.line_password.returnPressed.connect(self.try_login)

        login_layout.addStretch(1)
        login_layout.addLayout(id_layout)
        login_layout.addLayout(pw_layout)
        login_layout.addWidget(self.login_button)
        login_layout.addStretch(1)

        self.content_layout.addWidget(self.login_container)

    def try_login(self):
        user = self.line_id.text()
        password = self.line_password.text()
        
        logging.info(f'Attempting login for user: {user}')
        session, session_info, status_login = zyra.initsession(
            user, password, jira_url=CONFIG_DATA.get('jira_url', '')
        )
        
        if not status_login:
            QMessageBox.critical(self, "Login Fail", "Please check your ID/Password or internet connection.")
        else:
            CONFIG_DATA['id'] = user
            CONFIG_DATA['password'] = password
            configus.save_config(CONFIG_DATA, str(CONFIG_PATH))
            
            self.statusbar_status = 'logged in'
            self.switch_to_main_features(session, session_info)

    def switch_to_main_features(self, session, session_info):
        self.session = session
        self.session_info = session_info
        self.file_path = None

        self.setMinimumSize(700, 750)
        self.resize(700, 750)
        
        self.clear_content_area()



        main_features_box = QVBoxLayout()
        main_features_box.setSpacing(15)

        # --- [상단 영역: JIRA COMMANDS 조작 패널] ---
        top_panel_widget = QWidget()
        top_panel = QHBoxLayout(top_panel_widget)
        top_panel.setContentsMargins(0, 0, 0, 0)
        top_panel.setSpacing(20)

        cmd_layout = QVBoxLayout()
        cmd_layout.setSpacing(8)
        cmd_label = QLabel("JIRA COMMANDS")
        cmd_label.setProperty("class", "sectionLabel")
        self.btn_import_logwork = QPushButton('Import Logwork from File')
        self.btn_import_logwork.setFixedHeight(40)
        self.btn_import_logwork.setMinimumWidth(200)
        self.btn_import_logwork.clicked.connect(self.on_handle_action)
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.btn_import_logwork)
        cmd_layout.addStretch()
        top_panel.addLayout(cmd_layout)

        time_group = QVBoxLayout()
        time_group.setSpacing(5)

        date_layout = QHBoxLayout()
        self.label_date = QLabel('Date:')
        self.label_date.setFixedWidth(40)
        self.date_field = QDateEdit(QDate.currentDate())
        self.date_field.setCalendarPopup(True)
        self.date_field.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.label_date)
        date_layout.addWidget(self.date_field)
        time_group.addLayout(date_layout)

        start_layout = QHBoxLayout()
        self.label_start = QLabel('Start:')
        self.label_start.setFixedWidth(40)
        self.time_start = QTimeEdit(QTime.currentTime())
        self.time_start.setDisplayFormat("HH:mm:ss")
        self.btn_refresh_start = QPushButton('refresh')
        self.btn_refresh_start.setFixedWidth(65)
        self.btn_refresh_start.clicked.connect(self.sync_start_time)
        start_layout.addWidget(self.label_start)
        start_layout.addWidget(self.time_start)
        start_layout.addWidget(self.btn_refresh_start)
        time_group.addLayout(start_layout)

        end_layout = QHBoxLayout()
        self.label_end = QLabel('End:')
        self.label_end.setFixedWidth(40)
        self.time_end = QTimeEdit(QTime.currentTime())
        self.time_end.setDisplayFormat("HH:mm:ss")
        self.btn_refresh_end = QPushButton('refresh')
        self.btn_refresh_end.setFixedWidth(65)
        self.btn_refresh_end.clicked.connect(self.sync_end_time)
        end_layout.addWidget(self.label_end)
        end_layout.addWidget(self.time_end)
        end_layout.addWidget(self.btn_refresh_end)
        time_group.addLayout(end_layout)
        
        top_panel.addLayout(time_group)
        main_features_box.addWidget(top_panel_widget, 0)

        

        # --- [중앙 하단 영역: 오픈 태스크 패널 (아코디언 토글형)] ---
        self.task_panel_widget = QWidget()
        task_panel = QVBoxLayout(self.task_panel_widget)
        task_panel.setContentsMargins(0, 0, 0, 0)
        task_panel.setSpacing(5)

        task_header_layout = QHBoxLayout()
        self.label_open_task = QLabel('OPEN TASK')
        self.label_open_task.setProperty("class", "sectionLabel")
        
        self.btn_toggle_table = QPushButton('▼') 
        self.btn_toggle_table.setFixedWidth(35)
        self.btn_toggle_table.setFixedHeight(25)
        self.btn_toggle_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_toggle_table.clicked.connect(self.toggle_task_table)

        task_header_layout.addWidget(self.label_open_task)
        task_header_layout.addWidget(self.btn_toggle_table)
        task_header_layout.addStretch()
        task_panel.addLayout(task_header_layout)
        
        self.table_pending = QTableWidget()
        self.table_pending.setColumnCount(2)
        self.table_pending.setHorizontalHeaderLabels(['Task ID', 'Summary'])
        self.table_pending.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        #self.table_pending.setFixedHeight(140) 
        task_panel.addWidget(self.table_pending)
        
        main_features_box.addWidget(self.task_panel_widget, 1)

        # --- [최하단 영역: 로그 터미널 유동 영역] ---
        bottom_panel_widget = QWidget()
        bottom_panel = QVBoxLayout(bottom_panel_widget)
        bottom_panel.setContentsMargins(0, 0, 0, 0)
        bottom_panel.setSpacing(5)
        
        log_header = QLabel("LOG TERMINAL")
        log_header.setProperty("class", "sectionLabel")
        bottom_panel.addWidget(log_header)

        self.qtext_log_browser = QTextBrowser()
        self.qtext_log_browser.setProperty("class", "logLabel")
        self.qtext_log_browser.setFixedHeight(100)
        self.qtext_log_browser.setReadOnly(True)
        bottom_panel.addWidget(self.qtext_log_browser)

        main_features_box.addWidget(bottom_panel_widget, 0)
        
        self.content_layout.addLayout(main_features_box)

        self.load_jira_open_tasks()

        self.write_log(f"welcome to {CONFIG_DATA.get('id', '')}! :D")
        self.write_log('login succeed, please start logwork import~!')
        
        self.refresh_responsive_fonts()

    def load_jira_open_tasks(self):
        try:
            self.write_log("Fetching TQA_OD open tasks from Jira...")
            
            rh = zyra.Handler_Jira(self.session, jira_url=CONFIG_DATA.get('jira_url', ''))
            tickets_dict = _logwork_import.check_ticket_list_in_jira(rh)
            
            if not tickets_dict:
                self.table_pending.setRowCount(0)
                self.write_log("No active TQA_OD open tasks found.")
                return

            # 시그널 중복 연결 방지를 위해 잠시 연결 해제 후 재연결 준비
            try:
                self.table_pending.itemSelectionChanged.disconnect()
            except TypeError:
                pass

            self.table_pending.setRowCount(len(tickets_dict))
            self.table_pending.verticalHeader().setVisible(False)
            
            for row, (task_id, summary) in enumerate(tickets_dict.items()):
                # Column 0: Task ID (수정 불가, 선택은 가능)
                item_id = QTableWidgetItem(str(task_id))
                item_id.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table_pending.setItem(row, 0, item_id)
                
                # Column 1: Summary (수정 불가, 선택 불가)
                item_summary = QTableWidgetItem(str(summary))
                item_summary.setFlags(Qt.ItemFlag.ItemIsEnabled) # ItemIsSelectable를 제외하여 선택 방지
                self.table_pending.setItem(row, 1, item_summary)

            # 열 너비 비율 동적 설정
            header = self.table_pending.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            
            # 아이템 선택 변경 시그널 연결
            self.table_pending.itemSelectionChanged.connect(self.on_task_selected)
            
            self.write_log(f"Successfully loaded {len(tickets_dict)} open tasks.")
            
        except Exception as e:
            logging.error(f"Failed to load Jira tasks: {e}")
            self.write_log(f"Error loading open tasks: {str(e)}")
            self.table_pending.setRowCount(0)

    def clear_content_area(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def write_log(self, text):
        if hasattr(self, 'qtext_log_browser'):
            self.qtext_log_browser.append(text)
            self.qtext_log_browser.moveCursor(QTextCursor.MoveOperation.End)

    def     insert_sample_data(self):
        samples = [
            ("TASK-101", "Jira API Integration and OAuth Authentication"),
            ("TASK-102", "UI Design System Update and Color Palette Refactoring")
        ]
        self.table_pending.setRowCount(len(samples))
        for row, data in enumerate(samples):
            for col in range(2):
                item = QTableWidgetItem(data[col])
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_pending.setItem(row, col, item)

    @pyqtSlot()
    def on_task_selected(self):
        """ 테이블에서 Task ID가 선택되었을 때 변수를 업데이트하고 로그에 표시합니다. """
        selected_items = self.table_pending.selectedItems()
        if not selected_items:
            return
            
        selected_item = selected_items[0]
        col = selected_item.column()
        
        # 0번 열(Task ID)이 선택된 경우에만 변수 업데이트 및 로그 출력
        if col == 0:
            task_id = selected_item.text()
            
            # 메인 변수에 할당 (나중에 로그워크 넣을 때 self.selected_task_id로 바로 사용 가능)
            self.selected_task_id = task_id 
            
            self.write_log(f"Selected Task: {self.selected_task_id}")

    @pyqtSlot()
    def toggle_task_table(self):
        if self.table_pending.isVisible():
            self.table_pending.setVisible(False)
            self.btn_toggle_table.setText('▲')
            self.write_log("Open Task 목록 숨김")
        else:
            self.table_pending.setVisible(True)
            self.btn_toggle_table.setText('▼')
            self.write_log("Open Task 목록 펼침")

    @pyqtSlot()
    def sync_start_time(self):
        self.date_field.setDate(QDate.currentDate())
        self.time_start.setTime(QTime.currentTime())
        self.write_log("Date and Start Time updated.")

    @pyqtSlot()
    def sync_end_time(self):
        self.date_field.setDate(QDate.currentDate())
        self.time_end.setTime(QTime.currentTime())
        self.write_log("Date and End Time updated.")

    def open_filename_dialog(self):
        set_dir = CONFIG_DATA.get('last_file_path', '')
        if not set_dir:
            set_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
            
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Logwork", set_dir, "Excel Files (*.xlsx)", options=options
        )
        if file_name:
            folder_path = os.path.dirname(file_name)
            CONFIG_DATA['last_file_path'] = folder_path
            configus.save_config(CONFIG_DATA, str(CONFIG_PATH))
            return file_name
        return None

    @pyqtSlot()
    def on_handle_action(self):
        self.file_path = self.open_filename_dialog()
        if not self.file_path:
            self.write_log("please select file")
            return

        self.btn_import_logwork.setEnabled(False)
        self.statusbar_status = 'logwork importing~'
        
        self.worker = JiraImportWorker(self.session, self.file_path, CONFIG_DATA.get('jira_url', ''))
        self.worker.finished.connect(self.on_import_finished)
        self.worker.error_occurred.connect(self.on_import_error)
        self.worker.start()

    @pyqtSlot(str)
    def on_import_finished(self, final_status):
        self.statusbar_status = final_status
        self.write_log(final_status)
        self.btn_import_logwork.setEnabled(True)

    @pyqtSlot(str)
    def on_import_error(self, error_msg):
        self.write_log(error_msg)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText("□")
            self.centralWidget().setStyleSheet("#mainWidget { border-radius: 15px; }")
        else:
            self.showMaximized()
            self.max_btn.setText("❐")
            self.centralWidget().setStyleSheet("#mainWidget { border-radius: 0px; }")

    def update_statusbar_clock(self):
        current_time = QTime.currentTime().toString("hh:mm:ss")
        if hasattr(self, 'title_label'):
            self.title_label.setText(f"{self.title} \t [{current_time} - {self.statusbar_status}]")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_responsive_fonts()

    def refresh_responsive_fonts(self):
        dynamic_font_size = max(9, min(13, self.width() // 85))
        new_font = QFont()
        new_font.setPointSize(dynamic_font_size)

        for btn in self.findChildren(QPushButton):
            if btn.property("class") != "titleBtn":
                btn.setFont(new_font)
                if hasattr(self, 'btn_toggle_table') and btn == self.btn_toggle_table:
                    continue
                btn.setFixedHeight(int(dynamic_font_size * 2.6))

        for label in self.findChildren(QLabel):
            if label.property("class") == "sectionLabel":
                label.setFont(new_font)
        
        if hasattr(self, 'qtext_log_browser'):
            self.qtext_log_browser.setFont(new_font)
        if hasattr(self, 'table_pending'):
            self.table_pending.setFont(new_font)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            self.resize_edge = self._get_edge(event.position().toPoint())

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        edge = self._get_edge(pos)
        
        if edge == "top_left" or edge == "bottom_right":
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge == "top_right" or edge == "bottom_left":
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edge in ["left", "right"]:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge in ["top", "bottom"]:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        if self.drag_pos is not None:
            global_pos = event.globalPosition().toPoint()
            delta = global_pos - self.drag_pos
            rect = self.geometry()

            if self.resize_edge == "none":
                if pos.y() < 45:
                    self.move(self.pos() + delta)
                    self.drag_pos = global_pos
            else:
                if "left" in self.resize_edge:
                    rect.setLeft(rect.left() + delta.x())
                elif "right" in self.resize_edge:
                    rect.setRight(rect.right() + delta.x())
                if "top" in self.resize_edge:
                    rect.setTop(rect.top() + delta.y())
                elif "bottom" in self.resize_edge:
                    rect.setBottom(rect.bottom() + delta.y())
                
                if rect.width() >= self.minimumWidth() and rect.height() >= self.minimumHeight():
                    self.setGeometry(rect)
                    self.drag_pos = global_pos

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        self.resize_edge = "none"

    def _get_edge(self, pos):
        width = self.width()
        height = self.height()
        edge = ""
        if pos.x() <= self.MARGIN: edge += "left"
        elif pos.x() >= width - self.MARGIN: edge += "right"
        if pos.y() <= self.MARGIN: edge = "top_" + edge if edge else "top"
        elif pos.y() >= height - self.MARGIN: edge = "bottom_" + edge if edge else "bottom"
        return edge if edge else "none"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(title="Jira Management Tool v2.2")
    sys.exit(app.exec())