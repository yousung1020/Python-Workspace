from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests
from bs4 import BeautifulSoup

url = 'http://portal.dongyang.ac.kr/login_real.jsp?targetId=DoIT&RelayState=https://doit.dongyang.ac.kr/main/default.aspx'

browser = webdriver.Chrome("C:\chromedriver_win32\chromedriver.exe")

browser.implicitly_wait(10) # 페이지가 로딩될 때까지 최대 10초 기다림
browser.maximize_window() # 화면 최대화
browser.get(url)

id = browser.find_element(By.XPATH, '//*[@id="user_id"]')
id.click()
id.send_keys("") # 아이디 입력
time.sleep(1)

# pw = browser.find_element(By.CSS_SELECTOR, '#user_password')
pw = browser.find_element(By.XPATH, '//*[@id="user_password"]')
pw.click()
pw.send_keys("") # 비번 입력
time.sleep(1)

login_btn = browser.find_element(By.CSS_SELECTOR, '#loginFrm > div.btn_area > a')
login_btn.click()

browser.get('https://doit.dongyang.ac.kr/career/')

p_s = browser.page_source
soup = BeautifulSoup(p_s, "lxml")
p = soup.find_all('div', attrs={'class':'tit1'})
print("----------------------\n" + str(p) + "\n----------------------")

while True:
    pass
    time.sleep(3)
