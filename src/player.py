import util
import logging
import yao
from abc import ABC, abstractmethod
from src import ot


class YaoGarbler(ABC):
    """An abstract class for Yao garblers"""

    def __init__(self, circuit_file_path):
        circuits = util.parse_json(circuit_file_path)
        self.name = circuits["name"]
        self.circuits = []

        for circuit in circuits["circuits"]:
            garbled_circuit = yao.GarbledCircuit(circuit)
            p_bits = garbled_circuit.get_p_bits()
            entry = {
                "circuit": circuit,
                "garbled_circuit": garbled_circuit,
                "garbled_tables": garbled_circuit.get_garbled_tables(),
                "keys": garbled_circuit.get_keys(),
                "p_bits": p_bits,
                "p_bits_out": {
                    w: p_bits[w] for w in circuit["out"]
                }
            }
            self.circuits.append(entry)

    @abstractmethod
    def start(self):
        pass


class Alice(YaoGarbler):
    """
    Alice is the generator of the Yao circuit. (Garbler)

    Alice create a Yao circuit and sends it to the evaluator along with
    its encrypted inputs. Alice will finally print the truth table of
    the circuit for all combination of Alice-Bob inputs.

    Alice does not know Bob's inputs but for the purpose of printing
    the truth table only, Alice assumes that Bob's inputs follow a specific
    order.

    Attributes:
        circuits: the JSON file containing circuits
        oblivious_transfer: Optional; enable the Oblivious Transfer protocol (default true)
    """

    def __init__(self, circuits, oblivious_transfer=True):
        super().__init__(circuits)
        self.socket = util.GarblerSocket()
        self.ot = ot.ObliviousTransfer(self.socket, oblivious_transfer)

    def start(self):
        """
        Start Yao Protocol
        Returns:

        """
        for circuit in self.circuits:
            to_send = {
                "circuit": circuit["circuit"],
                "garbled_tables": circuit["garbled_tables"],
                "p_bits_out": circuit["p_bits_out"],
            }
            logging.debug(f"Sending {circuit['circuit']['id']}")
            self.socket.send_wait(to_send)
            self.print(circuit)

    def print(self, entry):
        """
        Print circuit evaluation for all Bob and Alice inputs
        :param entry:
        :return:
        """
        circuit, p_bits, keys = entry["circuit"], entry["p_bits"], entry["keys"]
        outputs = circuit["out"]
        a_wires = circuit.get("alice", [])  # Alice's wires
        a_inputs = {}  # map from Alice's wires to (key, encr_bit) inputs
        b_wires = circuit.get("bob", [])  # Bob's wires
        b_keys = {
            w: util.get_encr_bits(p_bits[w], key0, key1)
            for w, (key0, key1) in keys.items() if w in b_wires
        }
        input_count = len(a_wires) + len(b_wires)

        print(f"======== {circuit['id']} ========")

        # Generate all inputs for both Alice and Bob
        for bits in [format(n, 'b').zfill(input_count) for n in range(2 ** input_count)]:
            bits_a = [int(b) for b in bits[:len(a_wires)]]  # Alice's inputs

            # Map Alice's wires to (key, encr_bit)
            for i in range(len(a_wires)):
                a_inputs[a_wires[i]] = (keys[a_wires[i]][bits_a[i]],
                                        p_bits[a_wires[i]] ^ bits_a[i])

            # Send Alice's encrypted inputs and keys to Bob; retrieve result after evaluation
            result = self.ot.get_result(a_inputs, b_keys)

            # Format output
            str_bits_a = ' '.join(bits[:len(a_wires)])
            str_bits_b = ' '.join(bits[len(a_wires):])
            str_result = ' '.join([str(result[w]) for w in outputs])

            print(f"  Alice{a_wires} = {str_bits_a} "
                  f"Bob{b_wires} = {str_bits_b}  "
                  f"Outputs{outputs} = {str_result}")


class Bob:
    """
    Bob is the receiver and evaluator of the Yao circuit.

    Bob receives the Yao circuit from Alice, computes the results and sends them back.

    Attributes:
        oblivious_transfer: Optional; enable the Oblivious Transfer protocol (default true)
    """
    def __init__(self, oblivious_transfer=True):
        self.socket = util.EvaluatorSocket()
        self.ot = ot.ObliviousTransfer(self.socket, oblivious_transfer)

    def listen(self):
        """
        Start listening of Alice messages.
        :return:
        """
        logging.info("Start listening")
        while True:
            try:
                entry = self.socket.receive()
                self.socket.send(True)
                self.send_evaluation(entry)
            except KeyboardInterrupt:
                logging.info("Stop listening")
                break

    def send_evaluation(self, entry):
        """
        Evaluate yao circuit for all Bob and Alice's inputs and send back the results
        :param entry: A dict representing the circuit to evaluate
        :return:
        """
        circuit, p_bits_out = entry["circuit"], entry["p_bits_out"]
        garbled_tables = entry["garbled_tables"]
        a_wires = circuit.get("alice", [])  # list of Alice's wires
        b_wires = circuit.get("bob", [])  # list of Bob's wires
        input_count = len(a_wires) + len(b_wires)

        print(f"Received {circuit['id']}")

        # Generate all possible inputs for both Alice and Bob
        for bits in [format(n, 'b').zfill(input_count) for n in range(2**input_count)]:
            bits_b = [int(b) for b in bits[input_count - len(b_wires):]]  # Bob's inputs

            # Create dict mapping each wire of Bob to Bob's input
            b_inputs_clear = {
                b_wires[i]: bits_b[i]
                for i in range(len(b_wires))
            }

            # Evaluate and send result to Alice
            self.ot.send_result(circuit, garbled_tables, p_bits_out, b_inputs_clear)



