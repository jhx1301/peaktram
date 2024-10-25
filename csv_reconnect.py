import socket
import json
import hashlib
import base64
import csv
from datetime import datetime
import multiprocessing
import time  # 用于模拟长时间计算


def long_computation(data):
    # 这里加入你的 transformer 模型计算逻辑
    print(f"Long computation started with data: {data}")
    time.sleep(10)  # 模拟长时间计算
    print(f"Long computation completed with data: {data}")


# 校验码生成函数
def generate_verify_key(secret_key, timestamp, data):
    data_str = json.dumps(data, separators=(',', ':'))
    md5_str = hashlib.md5((secret_key + str(timestamp) + data_str).encode('utf-8')).hexdigest().upper()
    return md5_str


# 处理事件0和事件4的回覆
def handle_event(client_socket, evt, data_body):
    reply_status = 0
    message = "Success"

    if evt == 0:
        print("Received event 0")
        response_data = {
            "reply": reply_status,
            "message": message
        }
        client_socket.send(json.dumps(response_data).encode('utf-8'))

    elif evt == 4:
        print("Received event 4")
        rope = data_body.get('rope', '')
        alarm = data_body.get('alarm', '')
        pos = data_body.get('pos', '')
        value = data_body.get('value', '')
        level = data_body.get('level', '')

        # 存储到CSV文件
        with open('events.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([datetime.now(), rope, alarm, pos, value, level])

        response_data = {
            "reply": reply_status,
            "message": message
        }
        client_socket.send(json.dumps(response_data).encode('utf-8'))

        # 使用多进程处理长时间计算
        process = multiprocessing.Process(target=long_computation, args=(data_body,))
        process.start()



def handle_client(client_socket):

    timeout = 10  # 超时时间（秒）

    while True:
        try:
            client_socket.settimeout(timeout)
            data = client_socket.recv(2048)
            if not data:
                break

            json_data = json.loads(data.decode('utf-8'))
            evt = json_data.get('evt', -1)
            timestamp = json_data.get('time', 0)
            data_body = json_data.get('data', {})
            verify = json_data.get('verify', '')



            # 处理事件
            handle_event(client_socket, evt, data_body)

        except json.JSONDecodeError:
            print("Received data is not valid JSON!")
        except socket.timeout:
            print("Connection timeout!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

    client_socket.close()


def tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 9001))
    server_socket.listen(5)
    print("TCP Server is listening on port 9001...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established!")

        # 启动一个新进程处理客户端
        multiprocessing.Process(target=handle_client, args=(client_socket,)).start()


if __name__ == '__main__':
    tcp_server()
