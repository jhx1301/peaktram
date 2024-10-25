import json
import pytz
import base64
import csv
import threading
import queue
from datetime import datetime
from utils import generate_verify_code, parse_complete_json
from caches import PhotoDataCache, WaveformDataCache
import db_models
import socket
import time
import torch
import os
import cv2
from ultralytics import YOLO
import multiprocessing
from model.image_processor import process_image

# 图像处理工作过程函数
def image_processing_worker(task_queue, model_path, device):
    # 初始化模型
    model = YOLO(model_path)
    model.to(device)

    while True:
        try:
            image_path = task_queue.get(timeout=5)  # 获取任务，设置超时为5秒
            if image_path is None:  # 如果队列中收到结束标志，退出过程
                break

            # 调用外部模块的 process_image 函数来处理图像
            process_image(image_path, model, device)
            print(f"[*] Processed image: {image_path}")

        except queue.Empty:
            # 队列超时后休眠一段时间，防止不断尝试占用 CPU
            time.sleep(1)






class TCPClientHandler:
    def __init__(self, client_socket):
        self.client_socket = client_socket
        self.cache = PhotoDataCache()
        self.cache2 = WaveformDataCache()
        self.data_queue = queue.Queue()
        self.buffer = b""
        self.is_connected = True
        self.last_heartbeat_time = datetime.now()
        self.heartbeat_timeout = 10

        # 创建用于保存图像任务的队列
        self.save_task_queue = queue.Queue()

        # 创建用于保存数据库任务的队列
        self.db_task_queue = queue.Queue()

        # 检查设备，优先使用 GPU
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        # 加载 YOLO 模型
        relative_path_trained_model = "model/weights/best.pt"

        # 创建线程的集和
        self.threads = [
            threading.Thread(target=self.receive_data, daemon=True),
            threading.Thread(target=self.process_data, daemon=True),
            threading.Thread(target=self.check_heartbeat, daemon=True),
            threading.Thread(target=self.user_input_listener, daemon=True),
        ]

        # 创建保存图像的工作线程池
        for _ in range(2):  # 线程池大小可以根据需要调整
            save_worker_thread = threading.Thread(target=self.save_worker_function, daemon=True)
            self.threads.append(save_worker_thread)

        # 创建保存数据库的工作线程池
        for _ in range(2):  # 线程池大小可以根据需要调整
            db_worker_thread = threading.Thread(target=self.db_worker_function, daemon=True)
            self.threads.append(db_worker_thread)

        # 图像处理任务队列（multiprocessing.Queue 可以在过程间通信）
        self.image_task_queue = multiprocessing.Queue()

        # 创建图像处理过程
        self.image_process = multiprocessing.Process(
            target=image_processing_worker,
            args=(self.image_task_queue, relative_path_trained_model, self.device)
        )
        self.image_process.start()

        for thread in self.threads:
            thread.start()

        self.shutdown_event = threading.Event()
        while self.is_connected:
            time.sleep(1)


#处理发送数据的逻辑
    def send_data(self, event, data):
        hong_kong_tz = pytz.timezone('Asia/Hong_Kong')
        current_timestamp = int(datetime.now(hong_kong_tz).timestamp())
        verify_code = generate_verify_code('TCK.W', current_timestamp, data)

        request_data = {
            "data": data,
            "evt": event,
            "node": "001",
            "sn": "test",
            "time": current_timestamp,
            "verify": verify_code
        }

        request = json.dumps(request_data, separators=(',', ':'))
        self.client_socket.send(request.encode('utf-8'))
        print(f"Request for event {event} sent.")


#处理发送数据的逻辑
#todo：逻辑完善后，把手动发送数据的逻辑改成自动发送
    def user_input_listener(self):
        while self.is_connected:
            user_input = input().strip()
            if user_input == '8':
                self.send_data(8, {
                    "cameraIdx": 1,
                    "flawPos": 1,
                    "packFreq": 200,
                    "packLen": 1024,
                    "photoCnt": 1,
                    "recId": 1
                })
            elif user_input == '6':
                self.send_data(6, {
                    "packFreq": 100,
                    "packLen": 1024,
                    "recId": 1
                })

#接收数据，并且存储在队列里
    def receive_data(self):
        while self.is_connected:
            try:
                data = self.client_socket.recv(10000)
                if not data:
                    self.is_connected = False
                    break
                self.data_queue.put(data)
            except socket.timeout:
                continue  # 如果超时，继续循环，等待下一个接收
            except Exception as e:
                print(f"An error occurred while receiving data: {e}")
                self.is_connected = False
                break

        self.cleanup()

#套接字关闭的时候，处理关闭的逻辑
    def cleanup(self):
        self.shutdown_event.set()
        self.is_connected = False
        self.client_socket.close()  # 关闭客户端套接子
        print("Cleaned up resources.")

        # 向每个工作队列中发送 None，以便工作线程优雅地退出
        for _ in range(2):  # 保存图像工作线程数量
            self.save_task_queue.put(None)
        for _ in range(2):  # 保存数据库工作线程数量
            self.db_task_queue.put(None)

        # 向图像处理任务队列发送结束标志
        self.image_task_queue.put(None)

        # 等待图像处理过程结束
        self.image_process.join()

    #拆分buffer里面有效的json数据
    def process_data(self):
        while self.is_connected:
            while not self.data_queue.empty():
                self.buffer += self.data_queue.get()
                while True:
                    json_data, end_index = parse_complete_json(self.buffer)
                    if json_data is None:
                        break
                    self.buffer = self.buffer[end_index:]
                    self.handle_event(json_data)

    def check_heartbeat(self):
        while self.is_connected:
            current_time = datetime.now()

            if (current_time - self.last_heartbeat_time).total_seconds() > self.heartbeat_timeout:
                print("Heartbeat timeout. Closing connection.")
                self.is_connected = False
                break
            time.sleep(1)





#处理接收事件
    def handle_event(self, json_data):
        evt = json_data.get('evt', -1)
        data_body = json_data.get('data', {})
        time = json_data.get('time', -1)

        if evt == 0:  # 心跳包
            self.last_heartbeat_time = datetime.now()  # 更新心跳时间

        handlers = {
            0: self.handle_event_0,
            4: self.handle_event_4,
            5: self.handle_event_5,
            7: self.handle_event_7,
            9: self.handle_event_9,
            10: self.handle_event_10
        }
        handler = handlers.get(evt)
        if handler:
            handler(data_body, time)

    def handle_event_0(self, data_body, time):
        response_data = {"message": "Ok", "reply": 0}
        self.send_data(0, response_data)

    def handle_event_4(self, data_body, _):
        with open('events.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([datetime.now(), data_body.get('rope', ''),
                                 data_body.get('alarm', ''), data_body.get('pos', ''),
                                 data_body.get('value', ''), data_body.get('level', '')])


    def handle_event_7(self, data_body, time):
        recId = data_body.get('recId', 0)
        idx = data_body.get('idx', 0)
        cnt = data_body.get('cnt', 0)
        data_array = data_body.get('data', [])
        full_data = self.cache2.add_data(recId, idx, cnt, data_array)
        if full_data:
            self.db_task_queue.put(('event7', time, full_data))

    def handle_event_9(self, data_body, time):
        recId = data_body.get('recId', 0)
        flawPos = data_body.get('flawPos', 0.0)
        cameraIdx = data_body.get('cameraIdx', 0)
        photo_data = base64.b64decode(data_body.get('data', ''))
        print(data_body.get('packCnt', 1))
        full_data = self.cache.add_data(recId, flawPos, cameraIdx, data_body.get('packIdx', 1),
                                         data_body.get('packCnt', 1), photo_data)
        if full_data:
            # 将保存图像的任务提交到保存任务队列
            image_path = f"received_image_{time}.jpg"
            self.save_task_queue.put((image_path, full_data))

            # 将保存数据库的任务提交到数据库任务队列
            #self.db_task_queue.put(('event9', time, flawPos, full_data))

    def handle_event_10(self, data_body, _):
        recId = data_body.get('recId', 0)
        # todo:处理事件10的逻辑

    def handle_event_5(self, data_body, time):
        # 验证数据的完整性
        required_keys = ['recId', 'startTime', 'endTime', 'startPos', 'endPos', 'flawCnt', 'flawData']
        if not all(key in data_body for key in required_keys):
            print("Error: Missing required fields in event 5 data.")
            return

        # 提取数据
        recId = data_body['recId']
        startTime = data_body['startTime']
        endTime = data_body['endTime']
        startPos = data_body['startPos']
        endPos = data_body['endPos']
        flawCnt = data_body['flawCnt']
        flawData = data_body['flawData']

        # 处理损伤数据
        processed_flaw_data = []
        for flaw in flawData:

            flaw_info = {
                "rope_id": flaw[0],
                "damage_position": flaw[1],
                "damage_start": flaw[2],
                "damage_end": flaw[3],
                "damage_value": flaw[4],
                "severity": flaw[5],
                "camera_1_value": flaw[6],
                "camera_2_value": flaw[7],
                "camera_3_value": flaw[8]
            }
            processed_flaw_data.append(flaw_info)
        #todo：
        # 保存数据到数据库
        db_models.save_event5_data(recId, startTime, endTime, startPos, endPos, flawCnt, processed_flaw_data)

        print("Event 5 data processed and saved.")

        # 工作线程函数，负责从任务队列中获取任务并处理

    # 保存图像到临时文件的工作线程
    def save_worker_function(self):
        while self.is_connected:
            try:
                image_path, full_data = self.save_task_queue.get(timeout=5)  # 获取保存任务，设置超时为5秒
                if image_path is None:  # 如果队列中收到结束标志，退出线程
                    break

                # 保存图像到临时文件
                with open(image_path, 'wb') as img_file:
                    img_file.write(full_data)
                print(f"[*] Image saved to: {image_path}")

                # 将保存后的图像路径加入到处理任务队列中
                self.image_task_queue.put(image_path)
                self.save_task_queue.task_done()  # 标记保存任务完成

            except queue.Empty:
                # 队列超时后休眠一段时间，防止不断尝试占用 CPU
                time.sleep(5)




    # 数据库工作线程函数，负责保存数据库的任务
    def db_worker_function(self):
        while self.is_connected:
            try:
                db_task = self.db_task_queue.get(timeout=5)  # 获取任务，设置超时为5秒
                if db_task is None:  # 如果队列中收到结束标志，退出线程
                    break

                # 处理不同类型的数据库任务
                task_type = db_task[0]
                if task_type == 'event7':
                    _, task_time, full_data = db_task
                    db_models.save_event7_data(task_time, full_data)
                elif task_type == 'event9':
                    _, task_time, flawPos, full_data = db_task
                    db_models.save_event9_data(task_time, flawPos, full_data)
                elif task_type == 'event5':
                    _, task_time, recId, startTime, endTime, startPos, endPos, flawCnt, processed_flaw_data = db_task
                    db_models.save_event5_data(recId, startTime, endTime, startPos, endPos, flawCnt,
                                               processed_flaw_data)

                self.db_task_queue.task_done()  # 标记数据库任务完成

            except queue.Empty:
                # 队列超时后休眠一段时间，防止不断尝试占用 CPU
                time.sleep(5)