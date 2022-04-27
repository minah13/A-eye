# A-eye (인공지능 기술을 활용한 AI CCTV 어플리케이션)

## 소개

- 보안이 취약한 1인 가구를 위해 거주지의 안전을 위협하는 현상에 대해 애플리케이션을 통해 실시간으로 알림을 받을 수 있는 서비스를 제공
- 객체 인식 알고리즘을 통해 도난, 폭력을 감지할 수 있고, 얼굴 인식 알고리즘으로 사용자가 등록하지 않은 인물은 외부인으로 감지

### 구성도

![image](https://user-images.githubusercontent.com/50553183/165570380-6a828816-5a2f-496b-bac3-78b7c45fcbba.png)


### 주요 적용 기술

- Firebase Cloud Messaging
   : 안드로이드 사용자에게 위험 현상 감지 후 PUSH알림을 전송하기 위해 Firebase Cloud Messaging 서비스를 이용. 사용자는 Firebase Cloud로부터 해당 단말기에 대한 ID값을 받고, 획득한 ID를 웹서버로 보냄. 따라서 웹서버에서는 특정 사용자에게 알림 전송 가능.
- AWS
   : Amazon EC2 Ubuntu 인스턴스에 Apache 웹서버, MySQL 데이터베이스 서버, PHP 서버사이드 스크립트 언어, PHP와 MySQL 연동 라이브러리를 설치. 딥러닝 서버와 안드로이드 사용자와 직접 소켓 통신하며 위험 현상 알림과 DB제어의 중간다리 역할을 함.
- MySQL
   : 위험 현상 알림 기록과 안드로이드 사용자의 회원가입 정보 및 사용자별 사진을 DB에 저장함. PHP언어로 작성된 쿼리문을 통해 안드로이드 사용자는 데이터를 추가, 수정, 삭제하며 관리할 수 있고, 필요 시 원하는 데이터를 조회함. 
- mjpg-streamer
   : 라즈베리파이에 mjpg-streamer를 설치. 안드로이드 스튜디오 WebView를 통해 해당 라즈베리파이 URL에 접속하여 안드로이드 사용자가 라즈베리파이의 실시간 스트리밍 영상을 확인함.
- Docker
   : YOLOv3 개발 환경과 OpenFace 개발 환경의 의존성이 충돌하는 문제를 해결하기 위해서 각자 다른 가상환경에서 개발 진행. Docker 가상 환경 위에 OpenFace API를 활용.
- Anaconda
   : YOLOv3 개발 환경을 Anaconda 가상환경 위에 구축.

## 적용 알고리즘

### YOLOv3 : 객체 인식 알고리즘

![image](https://user-images.githubusercontent.com/50553183/165572657-aef65767-0e2f-4628-92d4-45a824200cdf.png)



### OpenFace : 얼굴 인식 알고리즘

![image](https://user-images.githubusercontent.com/50553183/165573119-869562bc-23da-4d86-a8cc-a0f1fe7d089f.png)


### 개발환경

- OS : Ubuntu 18.04 LTS, Android
- 개발도구 : Android Studio, MySQL(5.7.31), MySQL Workbench(8.0), Putty, Apache(2.4.29), Docker, Anaconda
- 개발언어 : Java, Python3, PHP(5.6.40)
- 기타사항 : AWS
- 디바이스 : 안드로이드 Galaxy S9, 라즈베리파이
- 통신 : 소켓 통신, HTTP 통신
- 형상관리 : GitLab(https://lab.hanium.or.kr/20_hf042/main), Ubuntu server

### 내가 맡은 부분

- 이미지 데이터 라벨링
- 라즈베리파이로부터 이미지를 받아 도난&배회자 감지(Yolov3 알고리즘 이용)
- 프레임 명도를 이용한 카메라 무력화 감지
- 범죄상황 발생시 프레임들을 이어 동영상 만들기
- 안드로이드 핸드폰으로 범죄상황 푸쉬알림 보내기

## 시연 동영상

https://www.youtube.com/watch?v=J-7w_T6IunQ

