from io import BytesIO
import socket
import sys

startBytes = b'\xFF\xFF\xFF\xFF'
endBytes = b'\n'

packetSize = 1024

class Console:
    host = ''
    port = ''
    password = ''
    
    is_connected = False

    sock = None

    def __init__(self, *, host, port=27015, password):
        self.host = host
        self.port = port
        self.password = password

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Создаем новый сокет
        self.sock.settimeout(4)
        try:
            self.sock.connect((self.host, int(self.port)))
            self.is_connected = True
            if self.execute('stats') == 'Bad rcon_password.':
                raise Exception("bad rcon password")
        except Exception as e:
            self.disconnect()  # Закрываем сокет в случае ошибки
            raise e  # Пробрасываем исключение дальше

    def disconnect(self):
        self.is_connected = False
        self.sock.close()

    def getChallenge(self):
        try:
            #Format message to server
            msg = BytesIO()
            msg.write(startBytes)
            msg.write(b'getchallenge')
            msg.write(endBytes)
            self.sock.send(msg.getvalue())

            response = BytesIO(self.sock.recv(packetSize))
            return str(response.getvalue()).split(" ")[1]
        except Exception as e:
            self.disconnect()
            raise Exception("server is offline")

    def execute(self, cmd):
        try:
            challenge = self.getChallenge()

            #Format message to server
            msg = BytesIO()
            msg.write(startBytes)
            msg.write('rcon '.encode())
            msg.write(challenge.encode())
            msg.write(b' ')
            msg.write(self.password.encode())
            msg.write(b' ')
            msg.write(cmd.encode())
            msg.write(endBytes)

            self.sock.send(msg.getvalue())
            response = BytesIO(self.sock.recv(packetSize))

            return response.getvalue()[5:-3].decode()
        except Exception as e:
            self.disconnect()
            raise Exception("server is offline")
