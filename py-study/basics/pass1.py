# 일반 유닛

class Unit:
    def __init__(self, name, hp, speed):
        self.name = name
        self.hp = hp
        self.speed = speed
    
    def move(self, location):
        print("[지상 유닛 이동]")
        print("{0} : {1} 방향으로 이동합니다. [속도 {2}]".format(self.name, location, self.speed))

# 공격 유닛

class AttackUnit(Unit): # AttackUnit 클래스는 Unit 클래스를 상속 받아 만들어짐. Unit 클래스 내용 사용 가능
    def __init__(self, name, hp, speed, damage):
        Unit.__init__(self, name, hp, speed) # Unit 클래스의 생성자를 호출 
        self.damage = damage
    
    def attack(self, location):
        print("{0} : {1} 방향으로 적군을 공격 합니다. [공격력 {2}]"\
            .format(self.name, location, self.damage))
    def damaged(self, damage):
        print("{0} : {1} 데미지를 입었습니다.".format(self.name, damage))
        self.hp -= damage
        print("{0} : 현재 체력은 {1} 입니다.".format(self.name, self.hp))
        if self.hp <= 0:
            print("{0} : 파괴되었습니다.".format(self.name))

# 파이어뱃: 공격 유닛

# firebat = AttackUnit("파이어뱃", 50, 16) # AttackUnit 클래스를 호출하고, firebat 변수에 할당 (AttackUnit의 인스턴스 변수)
# firebat.attack("5시") # AttackUnit 클래스 내의 attack 함수 호출

# 공격을 두 번 받는다고 가정
# firebat.damaged(25) 
# firebat.damaged(25)

# 드랍쉽: 공중 유닛

# 공중 유닛 클래스 (공격X)

class Flyable:
    def __init__(self, flying_speed):
        self.flying_speed = flying_speed # 멤버 변수 초기화

    def fly(self, name, location):
        print("{0} : {1} 방향으로 날아갑니다. [속도 {2}]".format(name, location, self.flying_speed))

# 공중 공격 유닛 클래스

class FlyableAttackUnit(AttackUnit, Flyable): # 클래스 상속을 두 개 이상 받음 (다중 상속)
    def __init__(self, name, hp, damage, flying_speed):
        AttackUnit.__init__(self, name, hp, 0, damage) # 지상 speed 0
        Flyable.__init__(self, flying_speed)
    
    def move(self, location):
        print("[공중 유닛 이동]")
        self.fly(self.name, location) # 오버라이딩

# 건물

class BuildingUnit(Unit):
    def __init__(self, name, hp, location):
        pass

# 서플라이 디폿

supply_depot = BuildingUnit("서플라이 디폿", 500, "7시")

def game_start():
    print("새로운 게임을 시작합니다.")

def game_over():
    pass

game_start()
game_over()