#!/usr/bin/python
import os
from PyQt5.QtWidgets import QFileDialog

from _src._api import config

# add event list
def open_fileName_dialog(title,config_path,logging):
    config_data =config.load_config(config_path)
    set_dir = config_data['last_file_path']
    if set_dir == '':
        set_dir = os.path.join(os.path.expanduser('~'),'Desktop')
        logging.info('folder path is %s' %set_dir)
    else:
        logging.info('folder path is %s' %set_dir)
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    file_name, _ = QFileDialog.getOpenFileName(title, set_dir, "Excel Files (*.xlsx)",options=options)
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
