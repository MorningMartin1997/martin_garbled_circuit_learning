import json

import zmq.sugar.socket

# SOCKET
LOCAL_PORT = 4080
SERVER_HOST = "localhost"
SERVER_PORT = 4080


class Socket:
    def __init__(self, socket_type):
        self.socket = zmq.Context().socket(socket_type)

    def send(self, msg):
        self.socket.send_pyobj(msg)

    def receive(self):
        return self.socket.recv_pyobj()

    def send_wait(self, msg):
        self.send(msg)
        return self.receive()


class EvaluatorSocket(Socket):
    def __init__(self, endpoint=f"tcp://*:{LOCAL_PORT}"):
        super(EvaluatorSocket, self).__init__(zmq.REP)
        self.socket.bind(endpoint)


class GarblerSocket(Socket):
    def __init__(self, endpoint=f"tcp://{SERVER_HOST}:{SERVER_PORT}"):
        super(GarblerSocket, self).__init__(zmq.REQ)
        self.socket.connect(endpoint)


def parse_json(json_path):
    with open(json_path) as json_file:
        return json.load(json_file)


def get_encr_bits(p_bit, key0, key1):
    return (key0, 0 ^ p_bit), (key1, 1 ^ p_bit)
