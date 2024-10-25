import socket

# 设置服务器的 IP 地址和端口号
HOST = '0.0.0.0'  # 监听所有可用的网络接口
PORT = 65432  # 选择一个非系统保留端口

# 创建一个 TCP/IP socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    # 绑定 socket 到地址和端口
    server_socket.bind((HOST, PORT))
    # 开始监听连接请求
    server_socket.listen()

    print(f"服务器正在监听 {HOST}:{PORT}...")

    while True:
        # 等待客户端连接
        conn, addr = server_socket.accept()
        with conn:
            print(f"连接来自 {addr}")

            while True:
                # 接收数据
                data = conn.recv(1024)
                if not data:
                    break
                print(f"接收到数据: {data.decode()}")

                # 发送响应数据
                response = "数据已收到"
                conn.sendall(response.encode())
