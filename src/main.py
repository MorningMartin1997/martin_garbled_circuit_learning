# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import logging
import util
import yao
from abc import ABC, abstractmethod

logging.basicConfig(format="[%(levelname)s] %(message)s",
                    level=logging.WARNING)

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

def main(
        party,
        circuit_path="circuits/bool.json",
        oblivious_transfer=True,
        print_mode="circuit",
        log_level=logging.WARNING,
):
    logging.getLogger().setLevel(log_level)

    if party == "alice":
        alice = Alice(circuit_path, oblivious_transfer=oblivious_transfer)
        alice.start()
    elif party = "bob":
        bob = Bob(oblivious_transfer=oblivious_transfer)
    else:
        logging.error(f"Unknown party '{party}'")

class Alice(YaoGarbler):
    """
    Alice is the generator of the Yao circuit. (Garbler)

    Alice create a Yao circuit and sends it to the evaluator along with
    its encrypted inputs. Alice will finally print the truth table of
    the circuit for all combination of Alice-Bob inputs.

    Alice does not know Bob's inputs but for the purpose of printing
    the truth table only, Alice assumes that Bob's inputs follow a specific
    order.
    """
    def __init__(self, circuits, oblivious_transfer=True):
        super().__init__(circuits)
        self.socket =

if __name__ == '__main__':
    import argparse

    def init():
        log_levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        parser = argparse.ArgumentParser(description="Run Yao Protocol.")
        parser.add_argument("party",
                            choices=["alice", "bob"],
                            help="the yao party to run")
        parser.add_argument(
            "-c",
            "--circuit",
            metavar="circuit.json",
            default="circuits/default.json",
            help="the JSON circuit file for alice and local tests",
        )
        parser.add_argument("--no-oblivious-transfer",
                            action="store_true",
                            help="disable oblivious transfer")
        parser.add_argument(
            "-m",
            metavar="mode",
            choices=["circuit", "table"],
            default="circuit",
            help="the print mode for local tests (default 'circuit')")

        parser.add_argument("-l",
                            "--loglevel",
                            metavar="level",
                            choices=log_levels.keys(),
                            default="warning",
                            help="the log level (default 'warning')")



