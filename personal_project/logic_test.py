from datetime import datetime, time
import asyncio 
now = datetime.now().time()

async def test():
    a = 3
    await asyncio.sleep(a+3)
    now = datetime.now().time()
    print(now)

print(now)
asyncio.run(test())
ZeroDivision
dda
dsa
dsadsa