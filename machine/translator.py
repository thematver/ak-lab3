import re
from typing import (
    List,
    Optional,
    Tuple,
)
from machine.isa import INSTRUCTION_TYPES, OperandType, Opcode, Operand, Instruction

NUMBER = r'-?[0-9]+'
LABEL = r'\.?[A-Za-z_]+'
STRING = r'^(\'.*\')|(\".*\")$'


def parse_label(val: str) -> Optional[str]:
    label = re.match(LABEL, val)
    if label:
        return label[0][:-1]
    return None


def parse_operand(operand: str) -> Operand:
    if parse_label(operand) or parse_label(operand[1:]):
        return Operand(OperandType.LABEL_TO_REPLACE, operand)
    elif operand.startswith('#'):
        return Operand(OperandType.CONSTANT, int(operand[1:]))
    elif operand.startswith('$'):
        return Operand(OperandType.INDIRECT_ADDRESS, int(operand[1:]))
    else:
        return Operand(OperandType.DIRECT_ADDRESS, int(operand))


def parse_instruction(line: str) -> Instruction:
    tokens = line.split()
    assert len(tokens) > 0, 'no tokens in the line'

    instr_type = INSTRUCTION_TYPES[tokens[0]]
    operand = None
    if len(tokens) == 2:
        operand = parse_operand(tokens[1])
    return Instruction(instr_type.opcode, operand)


def prepare_code(code: List[str]) -> str:
    prepared_code = map(lambda l: re.sub(r';.*', '', l), code)  # remove comments
    prepared_code = map(str.strip, prepared_code)  # remove indents
    prepared_code = filter(bool, prepared_code)  # remove empty lines
    prepared_code = map(lambda l: re.sub(r'\s+', ' ', l), prepared_code)  # remove extra spaces
    return '\n'.join(prepared_code)


def parse_data_block(data_block_text: str) -> Tuple[list, dict]:
    data_memory = []
    data_memory_map = {}
    for line in data_block_text.split('\n'):
        label, val = line.split(':', 1)
        if val.startswith(' word '):  # word 23
            data_memory_map[label] = len(data_memory)
            num = int(val[len(' word '):])
            data_memory.append(num)
        elif val.startswith(' db "'):  # db "string"
            data_memory_map[label] = len(data_memory)
            string = str(val[len(' db "'):-1]).replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
            for char in string:
                data_memory.append(ord(char))
        else:
            assert True, "unexpected value in data section"
    return data_memory, data_memory_map


def parse_text_block(text_block_text: str):
    labels_map = {}
    instructions = []
    for line in text_block_text.split('\n'):
        if ':' in line:
            label, *_ = map(str.strip, line.split(':', 1))
            labels_map[label] = len(instructions)
        else:
            instruction = parse_instruction(line)
            instructions.append(instruction)
    return instructions, labels_map


def update_instructions_with_labels(instructions: List[Instruction], data_labels: dict, code_labels: dict):
    new_instr = []
    for instruction in instructions:
        if instruction.operand and instruction.operand.type == OperandType.LABEL_TO_REPLACE:
            if INSTRUCTION_TYPES[instruction.opcode].is_data_operand:
                if instruction.operand.value.startswith('$'):
                    op = data_labels[instruction.operand.value[1:]]
                    new_instr.append(Instruction(instruction.opcode, Operand(OperandType.INDIRECT_ADDRESS, op)))
                else:
                    op = data_labels[instruction.operand.value]
                    new_instr.append(Instruction(instruction.opcode, Operand(OperandType.DIRECT_ADDRESS, op)))
            else:
                if instruction.operand.value.startswith('.'):
                    op = code_labels[instruction.operand.value[1:]]
                    new_instr.append(Instruction(instruction.opcode, Operand(OperandType.DIRECT_ADDRESS, op)))
                else:
                    op = code_labels[instruction.operand.value]
                    new_instr.append(Instruction(instruction.opcode, Operand(OperandType.DIRECT_ADDRESS, op)))

            if new_instr[-1].opcode == Opcode.ST or new_instr[-1].opcode == Opcode.JMP or \
                    new_instr[-1].opcode == Opcode.JE:  # dirty hack for st/jmp/je etc.
                if new_instr[-1].operand.type == OperandType.DIRECT_ADDRESS:
                    new_instr[-1] = Instruction(instruction.opcode, Operand(OperandType.CONSTANT, op))
                elif new_instr[-1].operand.type == OperandType.INDIRECT_ADDRESS:
                    new_instr[-1] = Instruction(instruction.opcode, Operand(OperandType.DIRECT_ADDRESS, op))
                else:
                    assert False, "something wrong with st/jmp/je "
        else:
            new_instr.append(instruction)
    return new_instr


def parse_code(code_text) -> Tuple[list[int], list[Instruction]]:
    code = prepare_code(code_text)
    data_index = code.find('section .data')
    assert data_index != -1, "no .data section in the code!"
    text_index = code.find('section .text')
    assert data_index != -1, "no .text section in the code!"

    if data_index < text_index:
        data_block = code[data_index + len('section .data') + 1: text_index - 1]
        text_block = code[text_index + len('section .text') + 1:]
    else:
        text_block = code[text_index + len('section .text') + 1: data_index - 1]
        data_block = code[data_index + len('section .data') + 1:]

    data_memory, data_memory_map = parse_data_block(data_block)
    instructions, instructions_labels_map = parse_text_block(text_block)
    replaced_instr = update_instructions_with_labels(instructions, data_memory_map, instructions_labels_map)
    return data_memory, replaced_instr
