from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import re
import os
import zipfile
import requests



#add internal libary
from . import loggas, configus

#make logpath
logging= loggas.logger

#loading config data
config_path = 'static\config\config.json'
selenium_path = 'static\config\selenium.json'
message_path = configus.load_config(config_path)['message_path']

#=================================================================================================
def get_chrome_ver_from_googlechromelabs(url = "https://googlechromelabs.github.io/chrome-for-testing/#stable"):
    newest_chorme_driver_downloader_url = ""
    r = requests.get(url)
    for i in r.text.split("<tr "):
        seached_all = re.findall('https.*chromedriver-win64.zip',i)
        if len(seached_all) > 0:
            newest_chorme_driver_downloader_url = seached_all[0]
            break
    return newest_chorme_driver_downloader_url

def download_chrome_dirver(file_name = None , url =None ):
    with open(file_name, "wb") as file:
        response = requests.get(url)
        file.write(response.content)
    zip_file = zipfile.ZipFile(file_name)
    zip_file.extractall(path=os.path.dirname(file_name))
    return 0

def get_chrome_driver(selenium_path=selenium_path):
    #road selenium config
    selenium_data = configus.load_config(selenium_path)
    chorme_driver_downloader = selenium_data['chrome_driver_down_path']
    googlechromelabs = selenium_data['googlechromelabs_github']
    chorme_driver_downloader_url = selenium_data['chorme_driver_downloader_url']
    
    #check insatlled driver version from chromelabs
    newest_chorme_driver_downloader_url = get_chrome_ver_from_googlechromelabs(url= googlechromelabs)

    if newest_chorme_driver_downloader_url == chorme_driver_downloader_url:
        logging.info(f'version is same - {newest_chorme_driver_downloader_url}')
        return 0
    else:
        logging.info(f'version is dfff')
        logging.info(f'current - {chorme_driver_downloader_url}')
        logging.info(f'new one - {newest_chorme_driver_downloader_url}')
        logging.info(f'start to exchange new one')
        download_chrome_dirver(file_name= chorme_driver_downloader, url=newest_chorme_driver_downloader_url)
        selenium_data['chorme_driver_downloader_url'] = newest_chorme_driver_downloader_url
        configus.save_config(selenium_data,selenium_path)
        return 0

def get_chrome_drive_version():
    chromedriver = r'C:\dev_python\Webdriver\chromedriver.exe'
    driver = webdriver.Chrome(chromedriver)
    print(driver.capabilities['browserVersion'])
    return 0

#=================================================================================================
# main function
def call_drivier(headless=None):
    #set up chromedriver
    selenium_data = configus.load_config(selenium_path)
    options = webdriver.ChromeOptions()
    #options.add_argument('disable-gpu')
    options.add_argument('lang=ko_KR')
    logging.info(headless)
    if headless == "False":
        logging.info(f'headless is {headless}')
        options.add_argument('headless') # HeadlessChrome 사용시 브라우저를 켜지않고 크롤링할 수 있게 해줌
    else:
        options.add_argument('window-size=1920x1080')

    #options.add_argument('User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36')
    # 헤더에 headless chrome 임을 나타내는 내용을 진짜 컴퓨터처럼 바꿔줌.
    try:
        logging.info('check chromedriver version')
        get_chrome_driver()
        driver = webdriver.Chrome(selenium_data["chromedriver"],options=options)
        return driver
    except:
        logging.info('loading chromedriver failed')
        return None
#=================================================================================================
#=============================== xpath handler ===================================================

def wait_xpath(driver, xpath):
    wait = WebDriverWait(driver, 30)
    wait.until(EC.visibility_of_element_located((By.XPATH,xpath)))
    return 0
    
def xpath_element_get_text(driver,xpath):
    status = False
    #wait_xpath(driver, xpath)
    try:
        xpath_element = driver.find_element("xpath",xpath)
        xpath_element_txt = xpath_element.text
        status = True
    except:
        logging.info(f'xpath_element_get_text - not found element')
        xpath_element_txt = None
    return status, xpath_element_txt

def xpath_element_click(driver,xpath):
    status = False
    #wait_xpath(driver, xpath)
    try:
        xpath_element = driver.find_element("xpath",xpath)
        xpath_element.click()
        status = True
    except:
        logging.info(f'xpath_element_click - not found element')
        xpath_element = None
    return status, xpath_element

def xpath_element_clear(driver,xpath):
    status = False
    #wait_xpath(driver, xpath)
    try:
        text_feild_xpath_comment_area =driver.find_element("xpath",xpath)
        text_feild_xpath_comment_area.clear()
        status = True
    except:
        logging.info(f'xpath_element_clear -not element clear')
        text_feild_xpath_comment_area = None
    return status, text_feild_xpath_comment_area
#=================================================================================================
#=================================================================================================