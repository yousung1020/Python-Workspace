input_num = int(input())

compare_num = input_num

cycle  = 0 # 카운트 횟수 초기값 지정

while (1):

    first_seat = compare_num % 10 # 일의 자리 값 추출 (입력 값을 10으로 나눈 후의 나머지)
    second_seat = compare_num // 10 # 십의 자리 값 추출 (입력 값을 10으로 나눈 후의 몫)
    add_num = (first_seat + second_seat) % 10 # 일의 자리 값과 십의 자리 값을 더한 후 10으로 나눈 나머지를 추출 (일의 자리)

    compare_num = (first_seat * 10) + add_num # 일의 자리를 10 곱하고 add_num 값을 더함

    cycle += 1 # 사이클 값 1 증가

    if(input_num == compare_num):
        break # 만약 사이클이 모두 지난 후 비교 값이 입력 값과 같으면 종료 반복문 탈출

print(cycle) # 사이클 값 출력