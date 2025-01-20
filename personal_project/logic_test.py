from datetime import datetime, time

now = datetime.now().time()

print(now > time(22, 0))