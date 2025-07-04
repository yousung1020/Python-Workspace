# 🔔 Discord 알림 봇 (Discord Notification Bot)

이 프로젝트는 지정된 시간에 Discord 채널에 알림 메시지를 보내는 파이썬 기반의 Discord 봇입니다. `discord.py` 라이브러리를 사용하여 Discord API와 상호작용하며, `asyncio`를 통해 비동기적으로 알림 기능을 수행합니다. 정해진 스케줄에 따라 사용자 정의 메시지를 보낼 수 있습니다.

## 🌟 주요 기능

* **Discord 봇 연동**: `discord.py` 라이브러리를 사용하여 Discord 봇 클라이언트를 초기화하고 Discord 서버에 연결합니다.
* **지정된 채널에 알림**: 특정 Discord 채널 ID를 설정하여 해당 채널로 메시지를 보낼 수 있습니다.
* **정시 알림 메시지 전송**:
    * 매시간 정각(00분 00초)에 미리 정의된 알림 메시지를 전송합니다.
    * 알림 메시지는 "정각 알림!! 🥳" 입니다.
    * 알림 전송 후 다음 정각까지 대기합니다.
* **봇 준비 상태 확인**: 봇이 Discord에 성공적으로 연결되고 준비되었을 때 콘솔에 메시지를 출력하여 상태를 확인할 수 있습니다.
* **비동기 작업 처리**: `asyncio`를 활용하여 알림 전송과 같은 작업을 비동기적으로 처리하여 봇의 다른 기능에 영향을 주지 않습니다.

## 🛠️ 기술 스택

* **언어**: Python
* **라이브러리**: `discord.py`, `asyncio`, `datetime`

## 🚀 프로젝트 실행 방법

프로젝트를 실행하려면 다음 단계를 따르세요.

1.  **필수 라이브러리 설치**:
    ```bash
    pip install discord.py
    ```
2.  **봇 토큰 설정**:
    * Discord 개발자 포털에서 봇을 생성하고 토큰을 발급받습니다.
    * `newAlramBot.py` 파일 내 `TOKEN = "YOUR_BOT_TOKEN"` 부분에 발급받은 봇 토큰을 입력합니다.
3.  **채널 ID 설정**:
    * 알림을 보낼 Discord 채널의 ID를 확인합니다.
    * `CHANNEL_ID = YOUR_CHANNEL_ID` 부분에 해당 채널 ID를 입력합니다.
4.  **봇 실행**:
    ```bash
    python newAlramBot.py
    ```

## ⚠️ 주의사항

* 봇 토큰은 외부에 노출되지 않도록 주의해야 합니다. 환경 변수로 관리하는 것을 권장합니다.
* 채널 ID는 봇이 메시지를 보낼 수 있는 권한이 있는 채널이어야 합니다.
