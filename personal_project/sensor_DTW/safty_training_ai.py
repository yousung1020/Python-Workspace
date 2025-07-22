import numpy as np

# df: data frame의 줄임말
import pandas as pd
import matplotlib.pyplot as plt
# dtw 계산
from dtaidistance import dtw_ndim
# 잡음 제거 필터
from scipy.signal import savgol_filter

# 각 센서의 값 변화를 그래프로 그려서 보여주는 함수
def graph_sensor_data(data_df, title="Sensor Data", show_plot=True):
    if data_df.empty:
        print(f"{title}을 그릴 데이터가 없습니다!")
        return
    
    # 센서의 갯수
    num_sensors = len(data_df.columns)

    # 그래프를 그릴 공간
    # 가로 15인치, 세로: 센서 갯수 * 2.5
    plt.figure(figsize=(15, num_sensors * 2.5))
    plt.suptitle(title, fontsize=16)

    # 각 칼럼별로 반복하면서 개별 그래프 그리기
    for i, col in enumerate(data_df.columns):
        plt.subplot(num_sensors, 1, i + 1)

        # 실제 그래프 그리기
        # index: 시간 흐름, data_df[col]: 해당 센서의 값
        plt.plot(data_df.index, data_df[col], label=col)

        # 각 센서 그래프의 작은 제목
        plt.title(f"{col}", loc="left", fontsize=12)

        # y축 이름
        plt.ylabel("값")

        # 그래프에 격자무늬 표시
        plt.grid(True, linestyle="--", alpha=0.6)

        # 각 선이 어떤 센서를 나타내는지 범례 표시
        plt.legend()
    
    plt.xlabel("프레임(시간)")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    if show_plot:
        plt.show()

# 2. 센서 데이터 다듬기(전처리)
def preprocess_sensor_data(data_df):
    # 처리할 데이터가 없으면 빈 배열 반환
    if data_df.empty:
        return np.array([])
    
    # window_length: 데이터를 얼마나 넓게(몇 프레임) 보고 부드럽게 할지 결정 (홀수여야 함)
    # 데이터 길이가 필터 윈도우 길이보다 짧으면 오류가 나므로, 최소값을 보장
    window_length = min(data_df.shape[0] - (data_df.shape[0] % 2 == 0), 11)

    if window_length < 3:
        window_length = 3

    # 모든 센서에 대해서 잡음 제거 필터 적용
    # 일반적으로 다항식 차수 3을 사용
    smoothed_data = data_df.apply(lambda col: savgol_filter(col, window_length, 3))

    # 값의 크기 통일(정규화): 0에서 1사이의 값으로 만들기
    # 정규화된 데이터를 저장할 빈 DataFrame 만들기
    normalized_data = pd.DataFrame(index=smoothed_data.index, columns=smoothed_data.columns)

    # 각 센서 별로 예상되는 최소/최대 값을 정해서 정규화
    for col in smoothed_data.columns:
        # 아래 if문들은 모두 가정 값들임. 실제 센서 값들의 범위를 쓸 것
        if "flex" in col:
            # flex 센서가 가지는 실제 데이터 범위
            s_min = 0
            s_max = 100
        elif "gyro" in col:
            s_min = -30
            s_max = 30
        # 다른 센서가 있다면 elif나 else를 추가하여 센서 추가!
    
        range_sensor = s_max - s_min # 센서 값의 전체 범위
        
        # (현재 센서 값 - 센서의 최소 값) / 센서의 전체 범위
        # 해당 과정을 거치면 모든 센서 값이 0에서 1사이로 맞추어짐
        normalized_data[col] = (smoothed_data[col] - s_min) / range_sensor
    
    # dtw 라이브러리는 numpy 배열을 더 선호하므로, DataFrame을 numpy 배열로 변환하여 반환하기
    return normalized_data.values

# 동작을 평가하는 실질적인 함수(해당 클래스가 처음 만들어질 때 실행되는 부분)
class MovementEvaluator:
    # reference_move: 모범 동작에 대한 센서 값(기준 값)
    # max_dtw: 완전히 틀린, 마지노선 dtw 거리 기준
    def __init__(self, reference_move, max_dtw):
        self.reference_move = reference_move
        self.max_dtw = max_dtw

        print("평가 준비 완료")
    
    # 사용자의 데이터를 전처리하는 메서드
    def preprocess_user_data(self, user_data_df):
        return preprocess_sensor_data(user_data_df)
    
    # 사용자의 동작을 실제로 평가하는 메인 함수
    def evaluator_user_movement(self, user_raw_data_df):
        # 사용자의 원본 데이터(user_raw_data_df) 전처리
        preprocessed_user_data = self.preprocess_user_data(user_raw_data_df)

        # 가장 작은 dtw 거리(가장 비슷한 구간)를 찾기 위한 초기값 셋팅
        min_dtw_distance = float("inf") # 무한대를 의미하는 가장 큰 숫자
        predicted_move = None # 예측된 동작 이름을 저장할 변수
        results = {} # 모든 모범 동작과의 dtw 거리를 저장할 딕셔너리

        # 저장된 모든 모범 동작과 사용자의 동작을 하나씩 비교
        for move_name, ref_data in self.reference_move.items():
            # dtw 라이브러리를 사용하여 두 동작의 다름 정도를 계산
            # window: dtw가 비교할 때 시간적으로 너무 멀어진 데이터끼리 억지로 맞추지 않도록 제한
            distance = dtw_ndim.distance(preprocessed_user_data, ref_data, window=10)
            results[move_name] = distance # 계산된 거리를 결과 딕셔너리에 저장

            # 현재까지 계산된 거리 중에 가장 작은 거리를 동작 찾기
            if distance < min_dtw_distance:
                min_dtw_distance = distance
                predicted_move = move_name
            
        # dtw 거리를 0~100% 정확도 점수로 바꾸기
        accuracy_percentage = 0.0 # 초기 정확도 0%

        # 만약에 예측된 동작이 있고, dtw 거리가 무한대가 아니라면
        if predicted_move and min_dtw_distance != float("inf"):
            normalized_distance = min_dtw_distance / self.max_dtw