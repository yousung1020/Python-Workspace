class Unit:
    def __init__(self):
        print("유닛 생성자")

class Flyable:
    def __init__(self):
        print("Flyable 생성자")

class FlyableUnit(Flyable, Unit): # 단일 상속을 받을 때엔 super를 이용하여 해당 클래스의 생성자 호출 가능, 다중 상속일 때는 X
    def __init__(self):
        # super().__init__()
        Unit.__init__(self)
        Flyable.__init__(self)

# 드랍쉽

dropship = FlyableUnit()