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

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __init__(self, *, host, port=27015, password):
        self.host = host
        self.port = port
        self.password = password

    def connect(self):
        self.sock.settimeout(4)
        self.sock.connect((self.host, int(self.port)))
        self.is_connected = True
        if self.execute('stats') == 'Bad rcon_password.':
            raise Exception("bad rcon password")
            self.disconnect()

    def disconnect(self):
        self.sock.close()
        self.is_connected = False

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
            raise Exception("server is offline")
            self.disconnect()

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
            raise Exception("server is offline")
            self.disconnect()