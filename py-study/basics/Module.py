# import theater_Module

# theater_Module.price(3) # 세 명이서 영화를 보러 갔을 때의 가격
# theater_Module.price_morning(4)
# theater_Module.price_soldier(2)

# import theater_Module as mv

# mv.price(3)

# from theater_Module import * # theater_Module 을 앞에 안붙여도 함수 사용 가능

# price(3)
# price_morning(4)
# price_soldier(5)

# from theater_Module import price, price_morning # 사용 할 함수 기능만 따로 지정하여 import 가능

# price_morning(5)
# price(3)

from theater_Module import price_soldier as price

price(5)