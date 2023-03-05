score = open("score.txt", "r", encoding="utf8")

lines = score.readlines() # list 형태로 저장

print(lines)

for line in lines:
    print(line, end="")
score.close()