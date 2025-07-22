# from datetime import datetime, time, timedelta
# import discord
# from discord.ext import commands
# # import asyncio 
# # now = datetime.now().time()
# intents = discord.Intents.default()
# intents.message_content = True
# bot = commands.Bot(command_prefix='!', intents=intents)

# @bot.event
# async def on_ready():
#     a = bot.get_channel()
#     b = "c"
#     c = b.replace("c", "yo")
#     print(b)
#     await a.send("📌ㅎㅇㅎㅇㅇ")

# bot.run("")


import requests
from bs4 import BeautifulSoup

data = requests.get("https://www.dongyang.ac.kr/dmu/4902/subview.do")
data_null = requests.get("https://www.dongyang.ac.kr/dmu/4902/subview.do?enc=Zm5jdDF8QEB8JTJGZGlldCUyRmRtdSUyRjEzJTJGdmlldy5kbyUzRm1vbmRheSUzRDIwMjUuMDMuMDMlMjZ3ZWVrJTNEbmV4dCUyNg%3D%3D")
data_null = BeautifulSoup(data_null.text, "lxml")

data_null = data_null.find_all("tr", attrs={"class":""})
del data_null[0:2]
data_null = data_null[0].find_all("td", attrs={"class":""})

yo2 = []
for i in data_null:
    i = i.get_text().strip()
    yo2.append(i)

for i in yo2:
    if (i == "-"):
        print("-입니다!")
    else:
        print("아닌뒈")

data = BeautifulSoup(data.text, "lxml")

data = data.find_all("tr", attrs={"class":""})
del data[0:2]
data1 = data
# data1 = data[1].find("td", attrs={"class":""})
data = data[0].find("td", attrs={"class":"highlight"}).get_text().strip().replace("[점심]", "")
data1 = data1[0].find_all("td")

yo = []
for i in data1:
    i = i.get_text().strip().replace("[점심]", "")
    if (i != "-"):
        yo.append(i)
    else:
        yo.append("메뉴가 비었습니다!")


# data1 = re.sub(r'\s+', ' ', data1).strip()

# print(data)
target = 0
for i in yo:
    print(yo[target])
    target += 1

