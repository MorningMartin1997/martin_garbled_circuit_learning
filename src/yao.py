import pickle
import random
from cryptography.fernet import Fernet


def encrypt(key, data):
    """
    Encrypt a message
    :param key: The encryption key
    :param data: The message to encrypt
    :return: The encrypted message as a byte stream
    """
    f = Fernet(key)
    return f.encrypt(data)


class GarbledGate:
    """
    A representation of a garbled gate.

    Args:
        gate: A dict containing gate spec.
        keys: A dict mapping each wire to a pair of keys
        p_bits: A dict mapping each wire to its p-bit
    """

    def __init__(self, gate, keys, p_bits):
        self.keys = keys
        self.p_bits = p_bits
        self.input = gate["in"]
        self.output = gate["id"]
        self.gate_type = gate["type"]
        self.garbled_table = {}
        # A clear representation of the garbled table for debugging purposes
        self.clear_garbled_table = {}

        switch = {
            "OR": lambda b1, b2: b1 or b2,
            "AND": lambda b1, b2: b1 and b2,
            "XOR": lambda b1, b2: b1 ^ b2,
            "NOR": lambda b1, b2: not (b1 or b2),
            "NAND": lambda b1, b2: not (b1 and b2),
            "XNOR": lambda b1, b2: not (b1 ^ b2)
        }

        # NOT gate is a special case since it has only one input
        if self.gate_type == "NOT":
            self._gen_garbled_table_not()
        else:
            operator = switch[self.gate_type]
            self._gen_garbled_table(operator)

    def _gen_garbled_table_not(self):
        inp, out = self.input[0], self.output

        # For each entry in the garbled table
        for encr_bit_in in (0, 1):
            # Retrieve original bit
            bit_in = encr_bit_in ^ self.p_bits[inp]
            # Compute output bit according to the gate type
            bit_out = int(not bit_in)
            # Compute encrypted bit with the p-bit table
            encr_bit_out = bit_out ^ self.p_bits[out]
            # Retrieve related keys
            key_in = self.keys[inp][bit_in]
            key_out = self.keys[out][bit_out]

            # Serialize the output key along with the encrypted bit
            msg = pickle.dumps((key_out, encr_bit_out))
            # Encrypt message and add it to the garbled circuit
            self.garbled_table[(encr_bit_in, )] = encrypt(key_in, msg)
            # Add to the clear table indexes of each key
            self.clear_garbled_table[(encr_bit_in, )] = [(inp, bit_in), (out, bit_out),
                                                         encr_bit_out]

    def _gen_garbled_table(self, operator):
        """
        Create the garbled table of a 2-input gate
        :param operator: The logical function of the 2-input gate
        :return:
        """
        in_a, in_b, out = self.input[0], self.input[1], self.output

        for encr_bit_a in (0, 1):
            for encr_bit_b in (0, 1):
                bit_a = encr_bit_a ^ self.p_bits[in_a]
                bit_b = encr_bit_b ^ self.p_bits[in_b]
                bit_out = int(operator(bit_a, bit_b))
                encr_bit_out = bit_out ^ self.p_bits[out]
                key_a = self.keys[in_a][bit_a]
                key_b = self.keys[in_b][bit_b]
                key_out = self.keys[out][bit_out]

                msg = pickle.dumps((key_out, encr_bit_out))
                self.garbled_table[(encr_bit_a, encr_bit_b)] = encrypt(
                    key_a, encrypt(key_b, msg))
                self.clear_garbled_table[(encr_bit_a, encr_bit_b)] = [
                    (in_a, bit_a), (in_b, bit_b), (out, bit_out), encr_bit_out
                ]

    def print_garbled_table(self):
        """Print a clear representation of the garbled table."""
        print(f"GATE: {self.output}, TYPE: {self.gate_type}")
        for k, v in self.clear_garbled_table.items():
            # If it's a 2-input gate
            if len(k) > 1:
                key_a, key_b, key_out = v[0], v[1], v[2]
                encr_bit_out = v[3]
                print(f"[{k[0]}, {k[1]}]: "
                      f"[{key_a[0]}, {key_a[1]}][{key_b[0]}, {key_b[1]}]"
                      f"([{key_out[0]}, {key_out[1]}], {encr_bit_out})")
            # Else it's a NOT gate
            else:
                key_in, key_out = v[0], v[1]
                encr_bit_out = v[2]
                print(f"[{k[0]}]: "
                      f"[{key_in[0]}, {key_in[1]}]"
                      f"([{key_out[0]}, {key_out[1]}], {encr_bit_out})")

    def get_garbled_table(self):
        """Return the garbled table of the gate."""
        return self.garbled_table


class GarbledCircuit:
    """
    A representation of a garbled circuit

    Args:
        circuit: A dict containing circuit spec
        p_bits: Optional; a dict of p-bits for the given circuit
    """
    def __init__(self, circuit, p_bits=None):
        if p_bits is None:
            p_bits = {}
        self.circuit = circuit
        self.gates = circuit["gates"]
        self.wires = set()

        self.p_bits = {}
        self.keys = {}
        self.garbled_tables = {}

        # Retrieve all wire IDs from the circuit
        for gate in self.gates:
            self.wires.add(gate["id"])
            self.wires.update(set(gate["in"]))
        self.wires = list(self.wires)

        self._gen_p_bits(p_bits)
        self._gen_keys()
        self._gen_garbled_tables()

    def _gen_p_bits(self, p_bits):
        """
        Create a dict mapping each wire to a random p-bit
        :param pbits: For debugging purpose, user can give determined p_bits
        :return:
        """
        if p_bits:
            self.p_bits = p_bits
        else:
            self.p_bits = {wire: random.randint(0, 1) for wire in self.wires}

    def _gen_keys(self):
        """
        Create pari of keys for each wire
        :return:
        """
        for wire in self.wires:
            self.keys[wire] = (Fernet.generate_key(), Fernet.generate_key())

    def _gen_garbled_tables(self):
        """
        Create the garbled table of each gate
        :return:
        """
        for gate in self.gates:
            garbled_gate = GarbledGate(gate, self.keys, self.p_bits)
            self.garbled_tables[gate["id"]] = garbled_gate.get_garbled_table()

    def print_garbled_tables(self):
        """
        Print p-bits and a clear representation of all garbled tables
        :return:
        """
        print(f"======== {self.circuit['id']} ========")
        print(f"P-BITS: {self.p_bits}")
        for gate in self.gates:
            garbled_table = GarbledGate(gate, self.keys, self.p_bits)
            garbled_table.print_garbled_table()
        print()

    def get_p_bits(self):
        """Return dict mapping each wire to its p-bit"""
        return self.p_bits

    def get_garbled_tables(self):
        """Return dict mapping each gate to its garbled table"""
        return self.garbled_tables

    def get_keys(self):
        """Return dict mapping each wire to its pair of keys"""
        return self.keys
