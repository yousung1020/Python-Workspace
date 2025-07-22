# import time
# import asyncio


# async def good_night():
#     # await asyncio.sleep(1)
#     print('잘자요')


# async def main():
#     await asyncio.gather(
#         good_night(),
#         good_night()

#     )
# print(f"start : {time.strftime('%X')}")
# asyncio.run(main())
# print(f"end : {time.strftime('%X')}")

# import time

# def good_night():
#   time.sleep(1)
#   print('잘자요')

# def main():
#   good_night()
#   good_night()


# print(f"start : {time.strftime('%X')}")
# main()
# print(f"end : {time.strftime('%X')}")

import asyncio

async def print_numbers():
    for i in range(10):
        print(i)
        await asyncio.sleep(1)

asyncio.run(print_numbers())