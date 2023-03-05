n = int(input())
h = 0
for i in range(1, n+1):
    n = list(map(int, str(i)))
    if i < 100:
        h += 1 
    elif n[0]-n[1] == n[1]-n[2]:
        h += 1  
print(h)