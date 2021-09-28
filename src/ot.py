import logging
import pickle

from src import yao


class ObliviousTransfer:
    def __init__(self, socket, enabled=True):
        self.socket = socket
        self.enabled = enabled

    def get_result(self, a_inputs, b_keys):
        """
        Send Alice's inputs and retrieve Bob's result of evaluation.
        :param a_inputs: A dict mapping Alice's wires to (key, encr_bit) inputs
        :param b_keys: A dict mapping each Bob's wire to a pair (key, encr_bit)
        :return: The result of the yao circuit evaluation
        """
        logging.debug("Sending inputs to Bob")
        self.socket.send(a_inputs)

        for _ in range(len(b_keys)):
            w = self.socket.receive()  # receive wire ID where to perform OT
            logging.debug(f"Received gate ID {w}")

            if self.enabled:
                pair = (pickle.dumps(b_keys[w][0]), pickle.dumps(b_keys[w][1]))
                self.ot_garbler(pair)
            else:
                to_send = (b_keys[w][0], b_keys[w][1])
                self.socket.send(to_send)

        return self.socket.receive()

    def send_result(self, circuit, g_tables, p_bits_out, b_inputs):
        """
        Evaluate circuit and send the result to Alice
        :param circuit: A dict containing circuit spec
        :param g_tables: Garbled tables of yao circuit
        :param p_bits_out: p-bits of outputs
        :param b_inputs: A dict mapping Bob's wires to (clear) input bits
        :return:
        """
        # map from Alice's wires to (key, encr_bit) inputs
        a_inputs = self.socket.receive()
        # map from Bob's wires to (key, encr_bit) inputs
        b_inputs_encr = {}

        logging.debug(f"Received Alice's inputs: {a_inputs}")

        for w, b_input in b_inputs.items():
            logging.debug(f"Sending wire ID {w}")
            self.socket.send(w)

            # Here the variable pair is in a specified order [clear input 0, clear input 1], so that we do not need ot
            # But in practice, we need ot to determine which key to choose
            pair = self.socket.receive()
            logging.debug(f"Received key pair, key {b_input} selected")
            b_inputs_encr[w] = pair[b_input]

        result = yao.evaluate(circuit, g_tables, p_bits_out, a_inputs, b_inputs_encr)
        self.socket.send(result)

    def ot_garbler(self, msgs):
        """
        Oblivious transfer, Alice's side
        :param msgs: A pair (msg1, msg2) to suggest to Bob.
        :return:
        """
        logging.debug("OT protocol started")

