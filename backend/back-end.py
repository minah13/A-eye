# -*- coding: utf-8 -*-
from ctypes import *
import mysql.connector
import math
import random
import socket
import cv2
import numpy as np
import time
import datetime
import darknet as dn
import colorsys
import threading
import os
from mysql.connector import Error
import base64
import face_recognition
from os.path import isfile, join


def sample(probs):
    s = sum(probs)
    probs = [a/s for a in probs]
    r = random.uniform(0, 1)
    for i in range(len(probs)):
        r = r - probs[i]
        if r <= 0:
            return i
    return len(probs)-1

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf : return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def c_array(ctype, values):
    arr = (ctype*len(values))()
    arr[:] = values
    return arr

class BOX(Structure):
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("w", c_float),
                ("h", c_float)]

class DETECTION(Structure):
    _fields_ = [("bbox", BOX),
                ("classes", c_int),
                ("prob", POINTER(c_float)),
                ("mask", POINTER(c_float)),
                ("objectness", c_float),
                ("sort_class", c_int)]


class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]

class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]

lib = CDLL("libdarknet.so", RTLD_GLOBAL)
lib.network_width.argtypes = [c_void_p]
lib.network_width.restype = c_int
lib.network_height.argtypes = [c_void_p]
lib.network_height.restype = c_int

predict = lib.network_predict
predict.argtypes = [c_void_p, POINTER(c_float)]
predict.restype = POINTER(c_float)

set_gpu = lib.cuda_set_device
set_gpu.argtypes = [c_int]

make_image = lib.make_image
make_image.argtypes = [c_int, c_int, c_int]
make_image.restype = IMAGE

get_network_boxes = lib.get_network_boxes
get_network_boxes.argtypes = [c_void_p, c_int, c_int, c_float, c_float, POINTER(c_int), c_int, POINTER(c_int)]
get_network_boxes.restype = POINTER(DETECTION)

make_network_boxes = lib.make_network_boxes
make_network_boxes.argtypes = [c_void_p]
make_network_boxes.restype = POINTER(DETECTION)

free_detections = lib.free_detections
free_detections.argtypes = [POINTER(DETECTION), c_int]

free_ptrs = lib.free_ptrs
free_ptrs.argtypes = [POINTER(c_void_p), c_int]

network_predict = lib.network_predict
network_predict.argtypes = [c_void_p, POINTER(c_float)]

reset_rnn = lib.reset_rnn
reset_rnn.argtypes = [c_void_p]

load_net = lib.load_network
load_net.argtypes = [c_char_p, c_char_p, c_int]
load_net.restype = c_void_p

do_nms_obj = lib.do_nms_obj
do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

do_nms_sort = lib.do_nms_sort
do_nms_sort.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

free_image = lib.free_image
free_image.argtypes = [IMAGE]

letterbox_image = lib.letterbox_image
letterbox_image.argtypes = [IMAGE, c_int, c_int]
letterbox_image.restype = IMAGE

load_meta = lib.get_metadata
lib.get_metadata.argtypes = [c_char_p]
lib.get_metadata.restype = METADATA

load_image = lib.load_image_color
load_image.argtypes = [c_char_p, c_int, c_int]
load_image.restype = IMAGE

rgbgr_image = lib.rgbgr_image
rgbgr_image.argtypes = [IMAGE]

predict_image = lib.network_predict_image
predict_image.argtypes = [c_void_p, IMAGE]
predict_image.restype = POINTER(c_float)

def classify(net, meta, im):
    out = predict_image(net, im)
    res = []
    for i in range(meta.classes):
        res.append((meta.names[i], out[i]))
    res = sorted(res, key=lambda x: -x[1])
    return res

def detect(net, meta, image, number,current, thresh=.5, hier_thresh=.5, nms=.45):
    im = load_image(image, 0, 0)
    num = c_int(0)
    pnum = pointer(num)
    predict_image(net, im)   #weight파일을 이용하여 이미지에 학습시킨 클래스가 있는지 예측
    #있다면 해당 bounding box의 위치,클래스,확률 등을 dets에 저장
    dets = get_network_boxes(net, im.w, im.h, thresh, hier_thresh, None, 0, pnum) 
    num = pnum[0]
    if (nms): do_nms_obj(dets, num, meta.classes, nms);

    res = [] #array that contains result of prediction
    
    # 현재 프레임에서 감지된 각 객체의 수  저장
    people_num = 0
    bicycle_num = 0 
    umbrella_num = 0
    pb_num = 0
    box_num = 0
    # 이전 프레임에서 감지된 각 객체의 수가 저장되어 있음
    global people
    global bicycle
    global umbrella
    global pb
    global box
    global people_detect
    global start_image
    global conn_d
    global user_id
    global image_repeat
    global face_multi
    global box_n
    global box_d
    global pb_n
    global pb_d
    global bicycle_n
    global bicycle_d
    global umbrella_n
    global umbrella_d

    for j in range(num):
        for i in range(meta.classes):
            if dets[j].prob[i] > 0:   # 학습시킨 객체가 감지되었다면
                b = dets[j].bbox
                res.append((meta.names[i], dets[j].prob[i], i))

                if i == 0:  # 사람 감지
                    people_num += 1
                    print("people Detected")
                elif i == 1:   # 자전거 감지
                    bicycle_num += 1
                    print("bicycle Detected")
                elif i == 2 :  # 우산 감지
                    umbrella_num += 1
                    print("umbrella Detected")
                elif i == 3 :  # 택배 봉투 감지
                    pb_num += 1
                    print("pb Detected")
                elif i == 4 :  # 택배 상자 감지
                    box_num += 1
                    print("box Detected")

    if people_num > 0 :
        people_detect.insert(0,1)       # 이미지에서 사람이 감지되었으므로 리스트에 1 삽입
        people = people + 1
        getRep(image,number)
        print("people : " + str(people))

    # 배회자 알림전송 후 60프레임이 지났다면,
    if ((number-start_image) == 59) or ((image_repeat == 1) and ((number + 7200 - start_image)== 59)):
        if people >= 40 :      # 60프레임 중 40프레임 이상 사람이 감지되었다면,
            if (face_image >= start_image and face_image <= number) or ((image_repeat == 1) and (face_image >= start_image) and (face_image <= (number + 7200))) or ((image_repeat == 1) and ((face_image + 7200) >= start_image) and (face_image <= number)) :      
                # 얼굴인식이 되었다면, 도커로 이미지 전송
                os.system("docker cp /home/hongik17/project/darknet/python/image" + str(face_image) + ".jpg hungry_elbakyan:/root/openface/python_code/fromDL/img" + str(face_image) + ".jpg")
                message = "fromDL/img"+str(face_image) + ".jpg"
                conn_d.send((str(len(message))).encode().ljust(16))
                conn_d.send(message.encode())
                if face_multi == 1 :
                    m = str(0)
                    conn_d.send(m.encode())
                    print("multi X")
                elif face_multi > 1 :
                    m = str(1)
                    conn_d.send(m.encode())
                    print("multi O")
                print("docker로 image 전송")
            else :
                print("배회자 알림 전송")
                giveAlert(10)           # 얼굴인식이 안된다면, 배회자 알림 전송
                f = open(image,"rb")
                f1 = f.read()
                t_people = threading.Thread(target=insertBLOB,args=(1,f1,user_id,current))
                t_people.start()
                f.close()

                t_v = threading.Thread(target=imagetovideo,args=(number,current,1))
                t_v.start()
            people = 0
            del people_detect[:]
            start_image = number + 1
            if start_image >= 7200 :
                start_image = start_image - 7200
        else :
            start_image = start_image + 1
            if start_image >= 7200 :
                start_image = strat_image - 7200
            pop_num = people_detect.pop()
            if pop_num == 1 :
                people = people - 1

    if people_num == 0 :
        people_detect.insert(0,0)

    if bicycle_d == 0 :
        if bicycle <= bicycle_num :
            bicycle_d = 0
        else :
            bicycle_n = 1
            bicycle_d = 1
    else :
        if bicycle >= bicycle_num :
            bicycle_n += 1
            if bicycle_n == 4 :
                giveAlert(30)     # 자전거 도난 알림
                if number == 0 :
                    f = open("image" + str(7199) + ".jpg","rb")
                else :
                    f = open("image" + str(number-1)+".jpg","rb")
                f1 = f.read()
                t_bicycle = threading.Thread(target=insertBLOB,args=(2,f1,user_id,current))
                t_bicycle.start()
                f.close()
                t_v = threading.Thread(target=imagetovideo,args=(number,current,2))
                t_v.start()
                bicycle_d = 0
                bicycle_n = 0
        else :
            bicycle_d = 0
            bicycle_n = 0

    bicycle = bicycle_num

    if umbrella_d == 0 :
        if umbrella <= umbrella_num :
            umbrella_d = 0
        else :
            umbrella_n = 1
            umbrella_d = 1
    else :
        if umbrella >= umbrella_num :
            umbrella_n += 1
            if umbrella_n == 4 :
                giveAlert(31)     # 우산 도난 알림
                if number == 0 :
                    f = open("image" + str(7199) + ".jpg","rb")
                else :
                    f = open("image" + str(number-1) + ".jpg","rb")
                f1 = f.read()
                t_umbrella = threading.Thread(target=insertBLOB,args=(2,f1,user_id,current))
                t_umbrella.start()

                f.close()
                t_v = threading.Thread(target=imagetovideo,args=(number,current,2))
                t_v.start()
                umbrella_d = 0
                umbrella_n = 0
        else :
            umbrella_d = 0
            umbrella_n = 0

    umbrella = umbrella_num


    if pb_d == 0 :
        if pb <= pb_num :
            pb_d = 0
        else :
            pb_n = 1
            pb_d = 1
    else :
        if pb >= pb_num :
            pb_n += 1
            if pb_n == 4 :
                giveAlert(32)     # 택배 봉투 도난 알림
                if number == 0 :
                    f = open("image" + str(7199) + ".jpg","rb")
                else :
                    f = open("image" + str(number-1) + ".jpg","rb")
                f1 = f.read()
                t_pb = threading.Thread(target=insertBLOB,args=(2,f1,user_id,current))
                t_pb.start()
                f.close()
                
                t_v = threading.Thread(target=imagetovideo,args=(number,current,2))
                t_v.start()
                pb_d = 0
                pb_n = 0
        else :
            pb_d = 0
            pb_n = 0

    pb = pb_num

    if box_d == 0  :  # 도난 의심 안할때
        if box <= box_num :
            box_d = 0
        else :
            box_n = 1
            box_d = 1
    else :
        if box >= box_num :
            box_n += 1
            if box_n == 4 :
                giveAlert(33)     # 택배 상자 도난 알림
                if number == 0 :
                    f = open("image" + str(7199) + ".jpg","rb")
                else :
                    f = open("image" + str(number-1) + ".jpg","rb")
                f1 = f.read()
                t_box = threading.Thread(target=insertBLOB,args=(2,f1,user_id,current))
                t_box.start()
                f.close()

                t_v = threading.Thread(target=imagetovideo,args=(number,current,2))
                t_v.start()
                box_d = 0
                box_n = 0
        else :
            box_d = 0
            box_n = 0


    box = box_num

    res = sorted(res, key=lambda x: -x[1])
    free_image(im)
    free_detections(dets, num)
    return res

# 출처 : https://pynative.com/python-mysql-blob-insert-retrieve-file-image-as-a-blob-in-mysql/
def insertBLOB(a_type, img,user_id,current) :
    try :
        connection = mysql.connector.connect(host = '54.180.122.226',database='project',user='hongik17',password='Hongik123!')
        cursor = connection.cursor()
        
        current_str = current.strftime('%Y-%m-%d %H:%M:%S')

        if a_type == 1 :
            sql_insert_blob_query = """INSERT INTO alert_list (user_id,alert_type, img, alert_time,stranger) VALUES (%s,%s,%s,%s,%s) """
            insert_blob_tuple = (user_id, a_type, img, current_str, 0)
        else :
            sql_insert_blob_query = """INSERT INTO alert_list (user_id, alert_type, img, alert_time) VALUES (%s,%s,%s,%s) """
            insert_blob_tuple = (user_id,a_type,img,current_str)
        result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
        connection.commit()

        cursor.close()
        connection.close()
        print("**************insertBLOB end*********************")
    except mysql.connector.Error as error :
        print("Failed inserting blob data into MYSQL table {}".format(error))

def giveAlert(c_index) :
    
    message = str(c_index)
    client_sock.send(message.encode())
    message1 = "Warning"
    if c_index/10 == 3 :
        message1 = "도난 감지"
    elif c_index/10 == 4 :
        message1 = "위험행위 감지"
    elif c_index == 2 :
        message1 = "무력화 감지"
    else:
        message1 = "배회자 감지"
    print(message1 + " : 알람전송")

def start_detect(net,meta,number,current) : 
    start = time.time()
    
    r = detect(net,meta,"image" + str(number) + ".jpg",number,current)
    end = time.time()
    print("Detect NUM : " + str(number))
    print(r)
    print("Yolo detect time : %s" % (end-start)) 
    print("\n")


def blind_func(number,current) :
    global blind
    r = None
    g = None
    b = None
    v = None
    
    start = time.time()
    img = cv2.imread("image" + str(number) + ".jpg")           # 이미지 이름 변경
    height = img.shape[0]
    width = img.shape[1]
    print("height => " + str(height) + " width => " +str(width))
        
    v_sum = 0.0
    count = 0.0
    i = 0
    j = 0

    while i < height :
        while j < width :
            b = img.item(i,j,0) #blue
            g = img.item(i,j,1) #green
            r = img.item(i,j,2) #red

            (x,y,v) = colorsys.rgb_to_hsv(r/255.,g/255.,b/255.)
            v_sum = v_sum + v
            j += 5
            count += 1
        i += 5

    if v_sum/count < 0.2 and blind == 0:
        
        giveAlert(2)
        f = open("image" + str(number) + ".jpg","rb")       # 이미지 이름 변경
        f1 = f.read()
        f1 = base64.b64encode(f.read())
        t_blind = threading.Thread(target=insertBLOB,args=("OUT",3,f1,user_id,current))
        t_blind.start()
        f.close()
        t_v = threading.Thread(target=imagetovideo,args=(number,current,3))
        t_v.start()
        print("\n\n\n*********************blind********************************\n")
    else :
        print("CAMERA IS OK NOW ^_____^ \n")

    end = time.time()
    print("Blind NUM : " + str(number))
    print("count : " + str(count))
    print("sum : " + str(v_sum))
    print("average of value : " + str(v_sum/count))
    print("BLIND time %s" % (end-start))


def yolo(conn,addr) :
    num = 0
    global image_repeat
    global user_id
    global end
    global detect_flag;

    while True :               # 라즈베리파이로부터 받아올 image 개수 ( while True로 고쳐야 함..)

        if num >= 7200 :
            image_repeat = 1
            num = 0
        if image_repeat == 1 :
            file_name = "image" + str(num) + ".jpg"
            if os.path.isfile(file_name) :
                os.remove(file_name)

        start_time = time.time()
        length = recvall(conn,16)
        if length == b'':
            end = 1
            break
        stringData = recvall(conn, int(length))
        current = datetime.datetime.now()                       # 프레임 찍힌 시간 저장(DB에 동영상 시간 넣기 위함)
        data = np.fromstring(stringData, dtype = 'uint8')
        frame = cv2.imdecode(data, cv2.IMREAD_COLOR)

        dest_jpg = "image" + str(num) + ".jpg"
        cv2.imwrite(dest_jpg, frame)
        end_time = time.time()

        print('Save image : ' + dest_jpg)
        print("SAVE IMAGE time %s \n" % (end_time - start_time))
        if detect_flag == True :
            t = threading.Thread(target=start_detect, args = (net,meta,num,current))    # 객체 인식 쓰레드
            t.start()
            t_b = threading.Thread(target=blind_func, args = (num,current))       # 무력화 감지 쓰레드
            t_b.start()
        
            t.join()
            t_b.join()

        num = num + 1


    print("*******************yolo end from rasp.***********************")

def getRep(imgPath,number) :          # 얼굴 감지 여부를 판단하는 함수
    global face_image
    global face_multi
    print("*******************Start Face detect**********************")

    face_locations = []
    rgb_small_frame = face_recognition.load_image_file(imgPath)

    face_locations = face_recognition.face_locations(rgb_small_frame)

    if not face_locations :
        print("Can't detect the face")
    if face_locations :
        print("FACE DETECTED!!!")
        face_image = number
        face_multi = 0
        for i in face_locations :
            face_multi += 1


def imagetovideo(num,current,type_info) :
    global user_id
    global image_repeat
    global video_num
    global blind
    global end
    
    if type_info != 3 or blind == 0 :
        if type_info == 3:
            blind = 1
        print("******#####################******Start Making Video*******############################********")
        start_time = current - datetime.timedelta(seconds=5)
        end_time = current + datetime.timedelta(seconds=5)
        start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
        current_str = current.strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        name = str(now.day) + str(now.hour) + str(now.minute) + str(now.second)
        video_url = "54.180.122.226/python1/video/" + name + ".mp4"

        current_video = video_num
        pathOut = name + ".avi"
        output_name = name + ".mp4"
        fps = 2
        video_num = video_num + 1

        frame_array = []
        num_start = num - 10
        num_end = num + 10
        if num_start < 0 :
            if image_repeat == 1 :
                num_start = num_start + 7200
            else :
                num_start = 0
        if num_end >= 7200 :
            num_end = num_end - 7200

        files = []
    
        if (num_end - num_start) < 0 :                       # 동영상 만들 이미지이름 리스트에 넣기
            for i in range(num_start,7199) :
                files.append("image" + str(i) + ".jpg")
            for i in range(0,num_end) :
                files.append("image" + str(i) + ".jpg")
        else :
            for i in range(num_start,num_end) :
                files.append("image" + str(i) + ".jpg")

        time.sleep(15)  # 이미지가 만들어질때까지 기다리기
        the_end = 0
        while True :
            if os.path.isfile("image" + str(num_end-1) + ".jpg") :
                break
            if end == 1:
                break
            time.sleep(1)
            the_end += 1
            if the_end == 60 :
                break


        if end != 1 and the_end != 60:
            for i in range(len(files)) :                  # 이미지 열어서 리스트 생성
                filename = files[i]
                img = cv2.imread(filename)
                height,width,layer = img.shape
                size = (width,height)
                frame_array.append(img)

            out = cv2.VideoWriter(pathOut, cv2.VideoWriter_fourcc(*'XVID'),fps,(1280,720))

            for i in range(len(frame_array)) :               
                out.write(frame_array[i])
            out.release()                                  # 동영상 생성
            
            os.popen("ffmpeg -i '{input}' -ac 2 -b:v 2000k -c:a aac -c:v libx264 -b:a 160k -vprofile high -bf 0 -strict experimental -f mp4 '{output}'".format(input = pathOut, output=output_name))

            comm = "scp -i ../../../newhongik17.pem " + output_name + " ubuntu@54.180.122.226:/home/project/python1/video/"
            os.system(comm)               # 동영상 웹서버로 전송

            print(str(current_video) + " : Video made....")
            if type_info == 3:
                blind = 0

            file_name = "image" + str(num) + ".jpg"
            if os.path.isfile(output_name) :
                os.remove(output_name)
            if os.path.isfile(pathOut) :
                os.remove(pathOut)

        try :                                   # alert_id 구하고 동영상정보 DB에 저장
            connection = mysql.connector.connect(host = '54.180.122.226',database='project',user='hongik17',password='Hongik123!')
            cursor = connection.cursor()
            sql_select_query = "select max(alert_id) from alert_list where user_id = '" + user_id + "' and alert_type = " + str(type_info) + ";"
            cursor.execute(sql_select_query)
            rows = cursor.fetchall()
            alert_id = int(rows[0][0])
            sql_insert_blob_query = """INSERT INTO video_list (alert_id,video_name,video_url,start_time,end_time) VALUES (%s,%s,%s,%s,%s) """
            insert_blob_tuple = (alert_id,output_name,video_url,start_str,end_str)
            result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
            connection.commit()

            connection.close()
            cursor.close()

        except mysql.connector.Error as error :
            print("Error {}".format(error))

def check_mod(client_sock) :
    global detect_flag
    while True :
        message = client_sock.recv(1024)
        num_d = message.decode()
        num = int(num_d)
        if num == 4 :
            detect_flag = True;
            print("*********경비모드 on(감지시작!)************")
        elif num == 5 :
            detect_flag = False;
            print("*********경비모드 off(감지중지!)************")

people = 0
bicycle = 0
umbrella = 0
box = 0
pb = 0
bicycle_d = 0
bicycle_n = 0
umbrella_d = 0
umbrella_n = 0
box_d = 0
box_n = 0
pb_d = 0
pb_n = 0

detect_flag = False;

end = 0
blind = 0
video_num = 0
face_image = -1               # 제일 최근 얼굴이 감지된 프레임 번호를 저장
start_image = 0              # 60프레임 중 첫 프레임의 번호를 저장
face_multi = 0

image_repeat = 0             # 1시간이 지나면 프레임번호 0으로 돌아가는데 1시간이 지났는지 여부를 저장(1이면 다시 0번부터 저장하고 있다는 의미)

people_detect = []           # 60프레임에 대해 사람 감지 여부를 0,1로 저장

#socket address (with aws server)
PORT_S = 9000
HOST_S = '54.180.122.226'

#socket address  (with rpi)
PORT = 10000
HOST = '192.168.123.100'

#socket address (with docker)
PORT_D = 10001

if __name__ == "__main__":
    
    #load files related with YOLO 
    net = load_net("../cfg/yolov3_theft.cfg","../backup_theft/yolov3_theft_40000.weights",0)
    meta = load_meta("../data/obj_theft.data")
    
    set_gpu(0)

    #AWS 서버와 소켓 연결(client 역할)
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((HOST_S,PORT_S))
    print("Connection Complete with aws server")

    global user_id
    message = client_sock.recv(1024)
    user = message.decode()
    print(user + " : send image")
    user_id = ''
    for i in range(len(user)) :
        tmp = user[i]
        print("tmp [" + str(i) + "] -> -" + tmp + "-")
        if i == 0:
            continue
        elif i == 1:
            continue
        else :
            user_id = user_id + str(tmp)
    print('user_id ->' + user_id)

    global conn_d
    # Docker와 소켓 연결(server 역할)
    sock_d = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_d.bind((HOST,PORT_D))
    sock_d.listen(10)
    conn_d,addr_d = sock_d.accept()
    print("Connection Complete with Docker")

    # Outdoor 라즈베리파이와 소켓 연결(server 역할)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')
    s.bind((HOST,PORT))

    print('Socket bind complete')
    s.listen(10)
    print('Socket now listening')

    conn,addr=s.accept()
    print('Connection Complete with rpi')

    t_android = threading.Thread(target=check_mode,args(client_sock))
    t_android.start()

    yolo(conn,addr)

