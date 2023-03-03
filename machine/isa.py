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

    def __repr__(self):
        return {
            OperandType.DIRECT_ADDRESS: "",
            OperandType.INDIRECT_ADDRESS: "$",
            OperandType.CONSTANT: "#",
            OperandType.LABEL_TO_REPLACE: ""
        }[self.type] + str(self.value)


@dataclass
class InstructionType:
    opcode: Opcode
    # true - при наличии операдна, может быть обращение по метке из секции .data
    # false - из секции .text
    is_data_operand: bool


@dataclass
class Instruction:
    opcode: Opcode
    operand: Optional[Operand]

    def __repr__(self):
        return str(self.opcode).split(".")[1] + ("" if self.operand is None else f" {self.operand.__repr__()}")


INSTRUCTION_TYPES = {
    'st': InstructionType(Opcode.ST, True),
    'ld': InstructionType(Opcode.LD, True),
    'add': InstructionType(Opcode.ADD, True),
    'div': InstructionType(Opcode.DIV, True),
    'mod': InstructionType(Opcode.MOD, True),

    'cmp': InstructionType(Opcode.CMP, True),

    'jmp': InstructionType(Opcode.JMP, False),
    'je': InstructionType(Opcode.JE, False),

    'in': InstructionType(Opcode.IN, False),
    'out': InstructionType(Opcode.OUT, False),
    'hlt': InstructionType(Opcode.HLT, False),
}


def instr_to_bin(instructions: [Instruction]) -> [bytes]:
    code = []
    for instr in instructions:
        opcode = list(Opcode).index(instr.opcode)
        operand_type = 0 if instr.operand is None else list(OperandType).index(instr.operand.type) + 1
        cmd = ((opcode << 3) + operand_type)
        code += [cmd.to_bytes(4, 'big', signed=False)]
        if operand_type > 0:
            # константы кодируются знаковым числом, адреса - беззнаковым
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
