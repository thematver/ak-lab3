import argparse
from json import dumps
import io

from machine.translator import parse_code
from machine.isa import encode_to_bytes


def main(input_file: io.TextIOWrapper, output_file: io.TextIOWrapper):
    code_text = input_file.readlines()
    data, code = parse_code(code_text)
    program = encode_to_bytes(data, code)
    for byte in program:
        output_file.write(byte)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='asm translator')
    parser.add_argument('input_file', type=argparse.FileType('r'), help='.asm file')
    parser.add_argument('output_file', type=argparse.FileType('wb'), help='.out file')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    main(args.input_file, args.output_file)
