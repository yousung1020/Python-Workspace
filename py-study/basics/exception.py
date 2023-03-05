try:
    print("나누기 전용 계산기")
    nums = []
    nums.append(int(input("첫 번째 숫자 입력: ")))
    nums.append(int(input("두 번째 숫자 입력: ")))
    # nums.append(int(nums[0] / nums[1]))

    print(f"{nums[0]} / {nums[1]} = {int(nums[2])}")
except ValueError: # 해당 에러에 대한 예외처리
    print("에러! 잘못된 값 입력!")
except ZeroDivisionError as err:
    print(err)
except Exception as err: # 지정한 오류를 제외한 모든 오류에 대한 메세지 출력
    print(err)

# except: # 지정한 오류를 제외한 모든 오류
#     print("알 수 없는 오류입니다!")