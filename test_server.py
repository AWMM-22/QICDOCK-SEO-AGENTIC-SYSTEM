import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('127.0.0.1', 8000))
s.listen(5)
print('Server listening on 127.0.0.1:8000')

while True:
    conn, addr = s.accept()
    print(f'Connection from {addr}')
    request = conn.recv(1024)
    print(f'Request: {request[:200]}')
    response = b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello World'
    conn.send(response)
    conn.close()