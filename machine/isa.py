from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, List, Union


class Opcode(str, Enum):
    IN = 'in'
    OUT = 'out'
    HLT = 'hlt'

    ST = 'st'
    LD = 'ld'
    ADD = 'add'
    DIV = 'div'
    MOD = 'mod'

    CMP = 'cmp'
    JMP = 'jmp'
    JE = 'je'


class OperandType(str, Enum):
    # прямая адресация
    DIRECT_ADDRESS = 'direct_address'
    # косвенная адресация
    INDIRECT_ADDRESS = 'indirect_address'
    CONSTANT = 'constant'
    # существует только на этапе трансляции и в его ходе заменяется на значение метки
    LABEL_TO_REPLACE = 'label_to_replace'


@dataclass
class Operand:
    type: OperandType
    value: Union[int, str]


@dataclass
class InstructionType:
    opcode: Opcode
    operands_count: int
    is_data_operand: Optional[bool]


@dataclass
class Instruction:
    opcode: Opcode
    operand: Optional[Operand]


INSTRUCTION_TYPES = {
    'in': InstructionType(Opcode.IN, 0, None),
    'out': InstructionType(Opcode.OUT, 0, None),
    'hlt': InstructionType(Opcode.HLT, 0, None),

    'st': InstructionType(Opcode.ST, 1, True),
    'ld': InstructionType(Opcode.LD, 1, True),
    'add': InstructionType(Opcode.ADD, 1, True),
    'div': InstructionType(Opcode.DIV, 1, True),
    'mod': InstructionType(Opcode.MOD, 1, True),

    'cmp': InstructionType(Opcode.CMP, 1, True),

    'jmp': InstructionType(Opcode.JMP, 1, False),
    'je': InstructionType(Opcode.JE, 1, False),
}


def instr_to_bin(instructions: [Instruction]) -> [bytes]:
    code = []
    for instr in instructions:
        opcode = list(Opcode).index(instr.opcode)
        operand_type = 0 if instr.operand is None else list(OperandType).index(instr.operand.type) + 1
        cmd = ((opcode << 3) + operand_type)
        code += [cmd.to_bytes(4, 'big', signed=False)]
        if operand_type > 0:
            code += [instr.operand.value.to_bytes(4, 'big', signed=instr.operand.type == OperandType.CONSTANT)]
            pass
    return code


def bin_to_instr(code: [bytes]) -> [Instruction]:
    instructions = []
    i = 0
    while i < len(code):
        cmd = int.from_bytes(code[i], 'big', signed=False)
        opcode = list(Opcode)[cmd >> 3]
        operand_type = cmd & 7
        operand = None
        if operand_type > 0:
            operand_type = list(OperandType)[operand_type - 1]
            i += 1
            value = int.from_bytes(code[i], 'big', signed=operand_type == OperandType.CONSTANT)
            operand = Operand(operand_type, value)
        instructions += [Instruction(opcode, operand)]
        i += 1
    return instructions


def decode_from_bytes(program: [bytes]) -> Tuple[List[int], List[Instruction]]:
    data_size = int.from_bytes(program[0], 'big', signed=False)
    data = [int.from_bytes(i, 'big', signed=True) for i in program[1:data_size + 1]]
    code = bin_to_instr(program[data_size + 1:])
    return data, code


def encode_to_bytes(data: [int], code: [Instruction]) -> [bytes]:
    return [len(data).to_bytes(4, 'big', signed=False)] + \
           [i.to_bytes(4, 'big', signed=True) for i in data] + \
           instr_to_bin(code)
