import aiohttp
from bs4 import BeautifulSoup
import asyncio
import re


async def fetch(session, url):
    async with session.get(url) as responce:
        return await responce.text()
    
async def main():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, 'https://www.dongyang.ac.kr/dmu_23218/1776/subview.do')
        soup = BeautifulSoup(html, 'lxml')
        ex = soup.find_all('tr', attrs={'class':''})
        ex.pop(0)
        a = ex[0].find('a')
        js_splits = re.findall("'([^']*)'", a['href'])
        print(js_splits)
        # ex = soup.find('td', attrs={'class':"td-subject"}).get_text()
        # divide = ex.split()
        # title_major = '제목: '
        # for i in (divide):
        #     title_major += i + ' '
        # print(title_major)

asyncio.run(main())

