import pytest

from machine.isa import Opcode, OperandType, Instruction, Operand
from machine.simulation import DataPath, ControlUnit


def simulate_until_finish(data, code, memsize, inp):
    dp = DataPath(memsize, data, inp)
    cu = ControlUnit(code, dp)

    try:
        while True:
            cu.decode_and_execute_instr()
    except StopIteration:
        return cu


@pytest.mark.parametrize("data, code, expected_acc", [
    (
            [6, 5],
            [
                Instruction(Opcode.LD, Operand(OperandType.CONSTANT, 3)),
                Instruction(Opcode.ADD, Operand(OperandType.CONSTANT, 5)),
                Instruction(Opcode.HLT, None)
            ],
            8,
    ),
    (
            [999, 777, 4, 888, 222],
            [
                Instruction(Opcode.LD, Operand(OperandType.DIRECT_ADDRESS, 4)),
                Instruction(Opcode.HLT, None)
            ],
            222,
    ),
    (
            [999, 777, 4, 888, 333],
            [
                Instruction(Opcode.LD, Operand(OperandType.INDIRECT_ADDRESS, 2)),
                Instruction(Opcode.HLT, None)
            ],
            333,
    ),
])
def test_addr(data, code, expected_acc):
    cu = simulate_until_finish(data, code, 10, [])
    assert cu.data_path.acc == expected_acc


@pytest.mark.parametrize("data, code, expected_acc", [
    (
            [],
            [
                Instruction(Opcode.JMP, Operand(OperandType.CONSTANT, 2)),
                Instruction(Opcode.JMP, Operand(OperandType.CONSTANT, 999)),
                Instruction(Opcode.ADD, Operand(OperandType.CONSTANT, 5)),
                Instruction(Opcode.HLT, None)
            ],
            5,
    ),
    (
            [],
            [
                Instruction(Opcode.LD, Operand(OperandType.CONSTANT, 2)),
                Instruction(Opcode.CMP, Operand(OperandType.CONSTANT, 2)),
                Instruction(Opcode.JE, Operand(OperandType.CONSTANT, 3)),
                Instruction(Opcode.HLT, None)
            ],
            2,
    ),
])
def test_jmp(data, code, expected_acc):
    cu = simulate_until_finish(data, code, 10, [])
    assert cu.data_path.acc == expected_acc
