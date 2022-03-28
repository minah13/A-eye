import socket
import threading
from pyfcm import FCMNotification
import requests
import time
import os
from os.path import isfile

def send_alarm(message_int) :

    global conn_num
    cctv_num = conn_num

    if message_int == 100 :
        message_body = " 등록한 사용자가 감지되었습니다. ^___^"
    elif message_int == 1 :  # 배회자(1)
        message_body = " * 배회자 * : 낯선 배회자가 감지되었습니다."
    elif message_int == 10 :
        message_body = " * 배회자 * : 얼굴이 보이지 않는 배회자가 감지되었습니다."
    elif message_int == 2 :  # 무력화(2)
        message_body = " * 카메라 무력화 * : 현관 앞 cctv에 문제가 발생했습니다."
    elif message_int == 30 :  # 도난 감지(3)
        message_body = " * 도난 * : 자전거가 도난되었습니다."
    elif message_int == 31 :
        message_body = " * 도난 * : 우산이 도난되었습니다."
    elif message_int == 32 :
        message_body = " * 도난 * : 택배봉투가 도난되었습니다."
    elif message_int == 33 :
        message_body = " * 도난 * : 택배상자가 도난되었습니다."
    elif message_int == 7 :  # train 완료(7)
        message_body = "이미지에 대한 학습이 끝났습니다. ^____^"
    elif message_int == 9 :  # retrain 완료(9)
        message_body = "이미지에 대한 재학습이 끝났습니다. ^____^"
    elif message_int == 11 : # 택배 도착(11)
        message_body = "문 앞에 택배가 도착했습니다. ^___^"

    message_title = "Alarm from yolocctvhi"
    print(message)
    print(message_body)

    global mToken
    mToken = mToken.rstrip() #개행문자 제거 

    # pyfcm라이브러리의 함수를 이용하여 해당 기기로 푸쉬알림 전송
    print(mToken)
    result = push_service.notify_single_device(registration_id = mToken, message_title = message_title, message_body = message_body)
    print(result)

def send_message(conn,message_int,pid) :
    message = str(message_int)
    conn.send(message.encode())

    if pid == 0:
        if message_int == 6 :
            print("train 시작 메세지 전송")
        elif message_int == 8 :
            print("retrain 시작 메세지 전송")
        elif message_int == 4 :
            print("경비모드 on 시작 메세지 전송")
        elif message_int == 5 :
            print("경비모드 off 시작 메세지 전송")
        elif message_int == 20 or message_int==21 or message_int == 22 or message_int == 23 :
            print("음성메세지 시작 메세지 전송")
    else :
        print("traing할 사람 수 :" + str(message_int))

def recv_message(conn,addr,conn_num) :
    global conn_docker
    global conn_android
    global conn_rp
    global user_id
    global conn_deep

    while True :
        message = conn.recv(1024)
        if message == b'':
            break
        message_d = message.decode()
        if conn_num ==0 or  conn_num >= 4 :
            message_b = message_d.encode()
            message_int = int.from_bytes(message_b,byteorder='big')
        else :
            message_int = int(message_d)
        
        if message_int == 100 or message_int == 1 or message_int == 10:        # 배회자
            send_alarm(message_int)
        elif message_int == 2 :     # 무력화
            send_alarm(message_int)
        elif message_int >= 30 and message_int <=34:     # 도난
            send_alarm(message_int)
        elif message_int ==4 :                   # 경비모드 on
            send_message(conn_deep,message_int,0)
        elif message_int == 5:                    # 경비모드 off
            send_message(conn_deep,message_int,0)
        elif message_int >= 61 and message_int <= 69:      # train 시작
            pid_num = message_int%10
            message_int = int(message_int/10)
            send_message(conn_docker,message_int,0)
            send_message(conn_docker,pid_num,1)
        elif message_int == 7 :     # train 끝
            send_alarm(message_int)
        elif message_int == 8 :     # retrain 시작
            send_message(conn_docker,message_int,0)
        elif message_int == 9 :     # retrain 끝
            send_alarm(message_int)
        elif message_int == 11 :    # 택배 도착 알림
            send_alarm(message_int)
        elif message_int == 20 :    # 음성 알림 시작1
            send_message(conn_rp,message_int,0)
        elif message_int == 21 :    # 2
            send_message(conn_rp,message_int,0)
        elif message_int == 22 :    # 3
            send_message(conn_rp,message_int,0)
        elif message_int == 23 :    # 4
            send_message(conn_rp,message_int,0)


push_service = FCMNotification(api_key="AAAA0H-XxIU:APA91bGTaoFyuAXCaY-Az_Owa-bTvEyMUYGCHrRuM3Wn7DNLMHXXOX4Ha0qy9WqiDhnXaklt4j6269fsQTGNVvmlO3Z78SGfk2WlSLYkjbKmLY3jYdCGDIleBaCoSWn-znet9YcUjcPe")

#socket address
PORT = 9000
HOST = '172.31.44.196'


if __name__ == "__main__" :

    global conn_num
    conn_num = 0
    global conn_deep
    global conn_docker
    global conn_android
    global conn_rp

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((HOST,PORT))
    print('Socket bind complete')
    s.listen(10)
    print('Socket now listening')

    global mToken  

    global user_id 

    while True :

        conn, addr = s.accept()

        if conn_num == 0:
            print("Connection Complete : Android")
            conn_android = conn
            message = conn.recv(1024)
            user_id = message.decode()
            print("user_ id : " + user_id)
            while True :
                if os.path.isfile("../sendtoken.txt") :
                    f = open("../sendtoken.txt","r")
                    mToken = f.readline()
                    print("token : " + mToken)
                    f.close()
                    break
        elif conn_num == 1 :
            print("Connection Complete : Deeplearning_server")
            conn_deep = conn
            conn_deep.send(user_id.encode())
        elif conn_num == 2 : 
            print("Connection Complete : Docker - train")
            conn_docker = conn
            conn_docker.send(user_id.encode())
        elif conn_num == 3:
            print("Connection Complete : RasberryPi")
            conn_rp = conn
        else :
            print("Connection Complete : Android")
            conn_android = conn
            conn_num = 4


        t = threading.Thread(target=recv_message, args = (conn,addr,conn_num))
        t.daemon = True
        t.start()
        conn_num += 1


