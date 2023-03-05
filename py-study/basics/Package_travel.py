# import travel.thailand

# trip_to = travel.thailand.TailandPackage()

# trip_to.detail()

# from travel.thailand import TailandPackage

# trip_to = TailandPackage()
# trip_to.detail()

from travel import *

# trip_to = thailand.TailandPackage()
# trip_to.detail()


# find package and module location

import inspect  # inspect: 검사하다, 점검하다
import random
import discord
from discord.ext import commands

print(inspect.getfile(random))  # random 모듈 파일이 어느 디렉토리에 있는지 확인
print(inspect.getfile(thailand))
print(inspect.getfile(discord))
