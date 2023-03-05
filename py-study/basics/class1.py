class Unit:
    def __init__(self, name, hp, damage): # __init__ : 생성자
        # 멤버 변수 선언
        self.name = name
        self.hp = hp
        self.damage = damage

        print("{0} 유닛이 생성 되었습니다.".format(self.name))
        print("체력 {0}, 공격력 {1}".format(self.hp, self.damage))

# marine1 = Unit("마린", 40, 5)
# marine2 = Unit("마린", 40, 5)
# tank = Unit("탱크", 150, 35)

wraith1 = Unit("레이스", 80, 5) # class의 init 생성자에 의한 결과 출력
print("유닛 이름 : {0}, 공격력 : {1}".format(wraith1.name, wraith1.damage)) # 클래스 외부에서의 클래스의 멤버 변수 출력

wraith2 = Unit("레이스", 80, 5)
wraith2.clocking = True # 클래스 외부에서 clocking 이라는 변수를 True 로 할당 wraith1 변수의 클래스에는 반영 X

if wraith2.clocking == True:
    print("{0} 는 현재 클로킹 상태입니다.".format(wraith2.name))

