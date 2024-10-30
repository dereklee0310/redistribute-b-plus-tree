"""B+ tree implementation in Python.

Usage: main.py
"""

import argparse
import logging
import sys

from bplustree import BPlusTree
from exceptions import *

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.ERROR)
logger = logging.getLogger()

ONE_TERM_COMMAND_PREFIXES = "Dq"
TWO_TERM_COMMAND_PREFIXES = "idf"


def setup_parser() -> None:
    """Build a custom parser for command line arguments."""
    parser = argparse.ArgumentParser(description="An interactive interface for B+ tree.")
    parser.add_argument(
        "-o", "--order", type=int, default=4, help="order of the b+ tree, default to 4"
    )
    parser.add_argument("-f", "--file", type=str, help="input file path")
    parser.add_argument(
        "-s",
        "--sequential",
        type=int,
        nargs="+",
        help="initialize B+ tree using sequential insertion",
    )
    parser.add_argument(
        "-b",
        "--bulk-load",
        type=int,
        nargs="+",
        help="initialize B+ tree using bulk loading",
    )
    return parser


def start_interative_interface(tree: BPlusTree) -> None:
    """Start a shell-like interactive session.

    :param tree: the one and only B+ tree :)
    :type tree: BPlusTree
    """
    print("Available commands:")
    print("Insert:  i <integer>")
    print("Delete:  d <integer>")
    print("Find   : f <integer>")
    print("Display: D")
    print("Quit:    q")
    while True:
        command = input(">>> ").strip()
        if not is_command_valid(command):
            print("Invalid command format, please try again.")
            continue
        run_command(tree, command)


def load_command_from_file(tree: BPlusTree, filename: str) -> None:
    """Run the commands in file line by line.

    :param tree: the one and only B+ tree :)
    :type tree: BPlusTree
    :param filename: file name of the test case
    :type filename: str
    """
    try:
        file = open(filename)
    except FileNotFoundError:
        print(f"File {filename} not found.")
        sys.exit()

    with file:
        commands = [line.strip() for line in file]
        for i, command in enumerate(commands):
            if not is_command_valid(command):
                print(f"Invalid command format at line {i + 1}: {command}")
                sys.exit()
            print(f">>> {command}")
            run_command(tree, command)


def is_command_valid(command: str) -> bool:
    """Check if the command format is valid.

    :param command: raw textline
    :type command: str
    :return: True if valid, False otherwise
    :rtype: bool
    """
    command_args = command.split(" ")
    length = len(command_args)

    if length == 1:
        if command_args[0] in ONE_TERM_COMMAND_PREFIXES:
            return True
    elif length == 2:
        if command_args[0] in TWO_TERM_COMMAND_PREFIXES and is_integer(command_args[1]):
            return True
    return False


# https://stackoverflow.com/questions/1265665/
def is_integer(s: str) -> bool:
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True


def run_command(tree: BPlusTree, command: str) -> None:
    """Parse and run the command.

    :param tree: the one and only B+ tree
    :type tree: BPlusTree
    :param command: raw textline
    :type command: str
    :raises NotImplementedError: _description_
    """
    command_args = command.split(" ")
    match command_args[0]:
        case "i":
            tree.insert(int(command_args[1]))
        case "d":
            tree.delete(int(command_args[1]))
        case "D":
            tree.display()
        case "f":
            tree.find(int(command_args[1]))
        case "q":
            sys.exit()
        case _:
            raise NotImplementedError


if __name__ == "__main__":
    logger.setLevel(logging.WARNING)
    args = setup_parser().parse_args()

    tree = BPlusTree(args.order)
    if args.sequential:
        tree.initialize(args.sequential)
    elif args.bulk_load:
        tree.bulk_load(args.bulk_load)

    if args.file is not None:
        load_command_from_file(tree, args.file)
    else:
        start_interative_interface(tree)

    # ---------------------------------------------------------------------------- #
    #                           tests for fast debugging                           #
    # ---------------------------------------------------------------------------- #
    # import random
    # random.seed(42)

    # ----------------------- test insertions and deletions ---------------------- #

    # list = [random.randint(0, 300) for i in range (150)]
    # list = random.sample(range(200), 200)
    # for i in list:
    #     tree.insert(i)
    # for i in list:
    #     print("delete", i)
    #     tree.delete(i)

    # ----------------------------- test bulk loading ---------------------------- #

    # list = list(range(30))
    # random.shuffle(list)
    # tree.bulk_load(list)
