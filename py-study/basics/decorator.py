def say_hi():
    print("hi!")
    print("zz")

def decorate(func):
    def wrapper(*args, **kwargs):
        print("before")
        func(*args, **kwargs)
        print("after")
    return wrapper

# without decorator

a = decorate(say_hi)
a()

@decorate
def say(msg):
    print(msg)

def bye():
    print("bye~")

say("how are you?")
bye()