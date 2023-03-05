import pickle

profile_file = open("profile.pickle", "wb")

profile = {"이름" : "최유성", "나이" : 20, "취미" : ["탁구", "코딩", "게임"]}

print(profile)

pickle.dump(profile, profile_file) # profile에 있는 정보를 file에 저장
profile_file.close()