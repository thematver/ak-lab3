from typing import List

import pytest

from machine.isa import Opcode, OperandType, Instruction, Operand, encode_to_bytes, decode_from_bytes
from machine.simulation import simulation
from machine.translator import parse_code


@pytest.mark.parametrize("code_filename, input_filename, journal_filename, data_expected, code_expected", [
    (
            "examples/hello.asm",
            "examples/hello_input.txt",
            "examples/hello_journal.txt",
            [1, 104, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100, 0],
            [Instruction(Opcode.LD, Operand(OperandType.INDIRECT_ADDRESS, 0)), Instruction(Opcode.CMP, Operand(OperandType.CONSTANT, 0)), Instruction(Opcode.JE, Operand(OperandType.CONSTANT, 8)), Instruction(Opcode.OUT, None), Instruction(Opcode.LD, Operand(OperandType.DIRECT_ADDRESS, 0)), Instruction(Opcode.ADD, Operand(OperandType.CONSTANT, 1)), Instruction(Opcode.ST, Operand(OperandType.CONSTANT, 0)), Instruction(Opcode.JMP, Operand(OperandType.CONSTANT, 0)), Instruction(Opcode.HLT, None)]
    ),
    (
            "examples/cat.asm",
            "examples/cat_input.txt",
            "examples/cat_journal.txt",
            [0],
            [Instruction(Opcode.IN, None), Instruction(Opcode.CMP, Operand(OperandType.DIRECT_ADDRESS, 0)), Instruction(Opcode.JE, Operand(OperandType.CONSTANT, 5)), Instruction(Opcode.OUT, None), Instruction(Opcode.JMP, Operand(OperandType.CONSTANT, 0)), Instruction(Opcode.HLT, None)]
    ),
    (
            "examples/prob5.asm",
            "examples/prob5_input.txt",
            "examples/prob5_journal.txt",
            [20, 20, 19],
            [Instruction(Opcode.LD, Operand(OperandType.DIRECT_ADDRESS, 0)), Instruction(Opcode.MOD, Operand(OperandType.DIRECT_ADDRESS, 2)), Instruction(Opcode.CMP, Operand(OperandType.CONSTANT, 0)), Instruction(Opcode.JE, Operand(OperandType.CONSTANT, 8)), Instruction(Opcode.LD, Operand(OperandType.DIRECT_ADDRESS, 0)), Instruction(Opcode.ADD, Operand(OperandType.DIRECT_ADDRESS, 1)), Instruction(Opcode.ST, Operand(OperandType.CONSTANT, 0)), Instruction(Opcode.JMP, Operand(OperandType.CONSTANT, 0)), Instruction(Opcode.LD, Operand(OperandType.DIRECT_ADDRESS, 0)), Instruction(Opcode.ST, Operand(OperandType.CONSTANT, 1)), Instruction(Opcode.LD, Operand(OperandType.DIRECT_ADDRESS, 2)), Instruction(Opcode.ADD, Operand(OperandType.CONSTANT, -1)), Instruction(Opcode.ST, Operand(OperandType.CONSTANT, 2)), Instruction(Opcode.CMP, Operand(OperandType.CONSTANT, 1)), Instruction(Opcode.JE, Operand(OperandType.CONSTANT, 16)), Instruction(Opcode.JMP, Operand(OperandType.CONSTANT, 0)), Instruction(Opcode.HLT, None)]
    ),
])
def test_golden(
        code_filename: str,
        input_filename: str,
        journal_filename: str,
        data_expected: List[int],
        code_expected: List[Instruction]
):
    with open(code_filename, 'r') as file:
        code_text = file.readlines()
        data, code = parse_code(code_text)
        program = encode_to_bytes(data, code)
    data, code = decode_from_bytes(program)
    assert data == data_expected
    assert code == code_expected
    with open(input_filename, 'r') as file:
        inp = list(file.read())
    journal = simulation(data, code, inp, 32, 1e4)
    print('\n' + journal)
    with open(journal_filename, 'r') as file:
        assert journal.strip() == file.read().strip()
