import requests
from bs4 import BeautifulSoup

session = requests.session()

login_data = {
    'user-name':'chldbtjd1020',
    'password':'cysjk1020@'
}

# session.post('http://portal.dongyang.ac.kr/login_real.jsp?targetId=DoIT&RelayState=https://doit.dongyang.ac.kr/main/default.aspx',\
#              data=login_data)

responce = session.get('https://doit.dongyang.ac.kr/Community/Notice/NoticeList.aspx')
print(responce)
soup = BeautifulSoup(responce, 'lxml')

a = soup.find_all('div', attrs={'class':'tit1'})

print(a)
