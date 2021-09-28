# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import logging

from src import player

logging.basicConfig(format="[%(levelname)s] %(message)s",
                    level=logging.WARNING)


def main(
        party,
        circuit_path="circuits/bool.json",
        oblivious_transfer=True,
        print_mode="circuit",
        log_level=logging.WARNING,
):
    logging.getLogger().setLevel(log_level)

    if party == "alice":
        alice = player.Alice(circuit_path, oblivious_transfer=oblivious_transfer)
        alice.start()
    elif party == "bob":
        bob = player.Bob()
        bob.listen()
    else:
        logging.error(f"Unknown party '{party}'")


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
        main(
            party=parser.parse_args().party,
            circuit_path=parser.parse_args().circuit,
            oblivious_transfer=not parser.parse_args().no_oblivious_transfer,
            print_mode=parser.parse_args().m,
            log_level=log_levels[parser.parse_args().loglevel],
        )


    init()
