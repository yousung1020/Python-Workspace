# from datetime import datetime, time
# import asyncio 
# now = datetime.now().time()

# async def test():
#     a = 3
#     await asyncio.sleep(a+3)
#     now = datetime.now().time()
#     print(now)

# print(now)
# asyncio.run(test())

for i in range(4):
    a = [1, 2, 3, 4]
    del a[0]
    print(a)


# name = "정통과 공지 함수"
#                     await pause_night()
#                     await asyncio.sleep(2)
#                     html_info_compared = await fetch(session, 'https://www.dongyang.ac.kr/dmu_23218/1776/subview.do', channels, name)
#                     soup_major_compared = BeautifulSoup(html_info_compared, 'lxml')
#                     major_num_compared = soup_major_compared.find_all('tr', attrs={'class':''})
#                     major_num_compared.pop(0)
#                     major_num_compared = major_num_compared[0].find().get_text()
#                     major_num_compared = int(major_num_compared.replace(" ", "").replace("\n", ""))

# name = "컴소과 공지 함수"
#                     await pause_night()
#                     html_info_compared = await fetch(session, 'http://www.dmu.ac.kr/dmu_23222/1797/subview.do', channels, name)
#                     soup_major_compared = BeautifulSoup(html_info_compared, 'lxml')
#                     major_num_compared = soup_major_compared.find_all('tr', attrs={'class':''})
#                     major_num_compared.pop(0)
#                     major_num_compared = int(major_num_compared[0].find("td", class_="td-num").get_text().replace(" ", "").replace("\n", ""))