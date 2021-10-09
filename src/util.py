import json
import operator
import random
import secrets

import sympy
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


# PRIME GROUP
PRIME_BITS = 64


def next_prime(num):
    return 3 if num < 3 else sympy.nextprime(num)


def gen_prime(num_bits):
    """
    Return random prime of bit size [num_bits]
    :param num_bits: bit size of prime
    :return:
    """
    r = secrets.randbits(num_bits)
    return next_prime(r)


def xor_bytes(seq1, seq2):
    """
    XOR two byte sequence
    """
    return bytes(map(operator.xor, seq1, seq2))


class PrimeGroup:
    """
    Cyclic Abelian group of prime order 'prime'
    """

    def __init__(self, prime=None):
        self.prime = prime or gen_prime(PRIME_BITS)
        self.prime_m1 = self.prime - 1
        self.prime_m2 = self.prime - 2
        self.generator = self.find_generator()

    def mul(self, num1, num2):
        """
        Multiply two numbers
        """
        return (num1 * num2) % self.prime

    def pow(self, base, exponent):
        """
        Compute nth power of an element
        """
        return pow(base, exponent, self.prime)

    def gen_pow(self, exponent):
        """
        Compute nth power of a generator
        """
        return pow(self.generator, exponent, self.prime)

    def rand_int(self):
        """
        :return: random int in [1, prime -1]
        """
        return random.randint(1, self.prime_m1)

    def inv(self, num):
        """
        Multiplicative inverse of an element
        """
        return pow(num, self.prime_m2, self.prime)

    def find_generator(self):
        """
        Find a random generator for the group
        :return:
        """
        # Find a random generator for the group
        factors = sympy.primefactors(self.prime_m1)

        while True:
            candidate = self.rand_int()
            for factor in factors:
                if 1 == self.pow(candidate, self.prime_m1 // factor):
                    break
                else:
                    return candidate


def parse_json(json_path):
    with open(json_path) as json_file:
        return json.load(json_file)


def get_encr_bits(p_bit, key0, key1):
    return (key0, 0 ^ p_bit), (key1, 1 ^ p_bit)
