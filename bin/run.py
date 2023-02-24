import argparse
import io

from machine.simulation import simulation
from machine.isa import decode_from_bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='asm translator')
    parser.add_argument('binary_file', type=argparse.FileType('rb'), help='.out file')
    parser.add_argument('input_file', type=argparse.FileType('r'), help='.txt file')
    return parser.parse_args()


def main(binary_file: io.TextIOWrapper, input_file: io.TextIOWrapper):
    word = binary_file.read(4)
    program = []
    while word:
        program += [word]
        word = binary_file.read(4)
    data, code = decode_from_bytes(program)
    inp = list(input_file.read())
    print(simulation(data, code, inp, 32, 1e4))


if __name__ == '__main__':
    args = parse_args()
    main(args.binary_file, args.input_file)
