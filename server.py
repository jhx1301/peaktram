import socket
from handlers import TCPClientHandler
import threading
def tcp_server(config):
    # 创建 TCP 套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((config['host'], config['port']))
    server_socket.listen(1)
    print(f"TCP Server is listening on {config['host']}:{config['port']}...")

    while True:
        try:
            print(2)
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr} has been established!")
            # 启动新线程处理连接
            client_handler_thread = threading.Thread(target=TCPClientHandler, args=(client_socket,))
            client_handler_thread.start()
            # 等待线程结束
            client_handler_thread.join()
            print(3)  # 线程结束后输出
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print(1)
            client_socket.close()  # 关闭客户端套接字
            print("Waiting for a new connection...")

if __name__ == '__main__':
    config = {
        'host': '127.0.0.1',  # 主机地址
        'port': 9001          # 端口号
    }
    tcp_server(config)


