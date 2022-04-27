# A-eye (인공지능 기술을 활용한 AI CCTV 어플리케이션)

## 소개

- 보안이 취약한 1인 가구를 위해 거주지의 안전을 위협하는 현상에 대해 애플리케이션을 통해 실시간으로 알림을 받을 수 있는 서비스를 제공
- 객체 인식 알고리즘을 통해 도난, 폭력을 감지할 수 있고, 얼굴 인식 알고리즘으로 사용자가 등록하지 않은 인물은 외부인으로 감지

## 구성도

![image](https://user-images.githubusercontent.com/50553183/165570380-6a828816-5a2f-496b-bac3-78b7c45fcbba.png)

## 주요 기능
- 도난 감지
- 배회자 감지
- CCTV 무력화 감지
- 경비모드 설정
- 위험 상황에 대한 푸쉬 알림 전송
- 인공지능 모델 재학습

## 적용 알고리즘

### YOLOv3 : 객체 인식 알고리즘

![image](https://user-images.githubusercontent.com/50553183/165572657-aef65767-0e2f-4628-92d4-45a824200cdf.png)



### OpenFace : 얼굴 인식 알고리즘

![image](https://user-images.githubusercontent.com/50553183/165573119-869562bc-23da-4d86-a8cc-a0f1fe7d089f.png)


## 개발환경

- OS : Ubuntu 18.04 LTS, Android
- 개발도구 : Android Studio, MySQL(5.7.31), MySQL Workbench(8.0), Putty, Apache(2.4.29), Docker, Anaconda
- 개발언어 : Java, Python3, PHP(5.6.40)
- 기타사항 : AWS
- 디바이스 : 안드로이드 Galaxy S9, 라즈베리파이
- 통신 : 소켓 통신, HTTP 통신
- 형상관리 : GitLab(https://lab.hanium.or.kr/20_hf042/main), Ubuntu server

## 주요 적용 기술

- Firebase Cloud Messaging
- AWS
- MySQL
- mjpg-streamer
- Docker
- Anaconda

## 내가 맡은 부분

- 이미지 데이터 라벨링
- 라즈베리파이로부터 이미지를 받아 도난&배회자 감지(Yolov3 알고리즘 이용)
- 프레임 명도를 이용한 카메라 무력화 감지
- 범죄상황 발생시 프레임들을 이어 동영상 만들기
- 안드로이드 핸드폰으로 범죄상황 푸쉬알림 보내기

## 시연 동영상

https://www.youtube.com/watch?v=J-7w_T6IunQ

