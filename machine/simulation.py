import os

from machine.isa import Opcode, OperandType, Instruction


class DataPath:
    def __init__(self, memory_size: int, data_mem_init_state: [int], input_buffer: [str]):
        self.min_val: int = -2 ** 31
        self.max_val: int = 2 ** 31 - 1

        self.data_mem = [0] * memory_size

        self.input_buffer = input_buffer
        self.output_buffer: [str] = []
        self.journal: [str] = []

        self.acc = 0
        self.zero = True
        self.address_reg = 0
        self.data_reg = 0
        for i, val in enumerate(data_mem_init_state):
            self.data_mem[i] = val

    def set_flags(self, val):
        self.zero = val == 0

    def has_next_input_token(self):
        return len(self.input_buffer)

    def next_input_token(self):
        return ord(self.input_buffer.pop(0))

    def is_zero(self) -> bool:
        return self.zero

    def address_reg_set(self, value: int):
        assert self.min_val <= value <= self.max_val, "overflow occurred"
        self.address_reg = value

    def data_reg_put(self, value: int):
        assert self.min_val <= value <= self.max_val, "overflow occurred"
        self.data_reg = value

    def latch_mem(self):
        self.data_mem[self.address_reg] = self.acc

    def latch_acc(self, from_mem=True):
        if from_mem:
            self.acc = self.data_mem[self.address_reg]
        else:
            self.acc = self.data_reg

    def latch_data_reg(self):
        self.data_reg = self.data_mem[self.address_reg]

    def acc_wr(self, sel: Opcode):
        if sel in {Opcode.ADD}:
            self.acc = self.__alu()
        if sel == Opcode.DIV:
            self.acc = self.acc / self.data_reg
        if sel == Opcode.MOD:
            self.acc = self.acc % self.data_reg

    def __alu(self):
        result = self.acc + self.data_reg
        if result > self.max_val:
            result = self.min_val + (result - self.max_val) - 1
        if result < self.min_val:
            result = self.max_val - (self.min_val - result) + 1
        return result

    def output(self):
        symbol = chr(self.acc)
        self.journal.append(f"{{new output symbol '{symbol}' will be added to {repr(''.join(self.output_buffer))}}}")
        self.output_buffer.append(symbol)


class ControlUnit:

    def __init__(self, code: [Instruction], data_path: DataPath):
        self.code = code
        self.instr_ptr = 0
        self.data_path = data_path
        self._tick = 0

    def current_tick(self):
        return self._tick

    def get_operand(self, instr: Instruction):
        if instr.operand is None:
            return None
        op_type = instr.operand.type
        op_arg = instr.operand.value
        if op_type == OperandType.CONSTANT:
            self.data_path.data_reg_put(op_arg)
            return op_arg
        if op_type == OperandType.DIRECT_ADDRESS:
            self.data_path.address_reg_set(op_arg)
            self.data_path.latch_data_reg()
            self._tick += 1
            return self.data_path.data_reg
        if op_type == OperandType.INDIRECT_ADDRESS:
            self.data_path.address_reg_set(op_arg)
            self.data_path.latch_data_reg()
            self._tick += 1
            self.data_path.address_reg_set(self.data_path.data_reg)
            self.data_path.latch_data_reg()
            self._tick += 1
            return self.data_path.data_reg

    def latch_instr_ptr(self, sel_next):
        if sel_next:
            self.instr_ptr += 1
        else:
            instr = self.code[self.instr_ptr]
            arg = self.get_operand(instr)
            self.instr_ptr = arg

    def decode_and_execute_instr(self):
        instr = self.code[self.instr_ptr]
        self.data_path.journal.append(f"{{executing: {instr}}}")
        opcode = instr.opcode

        if opcode == Opcode.LD:
            self.get_operand(instr)
            self.data_path.latch_acc(instr.operand.type != OperandType.CONSTANT.value)
            self.latch_instr_ptr(sel_next=True)
            self._tick += 1
        elif opcode == Opcode.ST:
            self.data_path.address_reg_set(self.get_operand(instr))
            self.data_path.latch_mem()
            self.latch_instr_ptr(sel_next=True)
            self._tick += 1
        elif opcode == Opcode.OUT:
            self.data_path.output()
            self._tick += 1
            self.latch_instr_ptr(sel_next=True)
            self._tick += 1
        elif opcode == Opcode.IN:
            if self.data_path.has_next_input_token() == 0:
                raise EOFError
            self.data_path.acc = self.data_path.next_input_token()
            self._tick += 1
            self.latch_instr_ptr(sel_next=True)
            self._tick += 1
        elif opcode == Opcode.ADD or opcode == Opcode.MOD or opcode == Opcode.DIV:
            self.get_operand(instr)
            self.data_path.acc_wr(opcode)
            self._tick += 1
            self.latch_instr_ptr(sel_next=True)
            self._tick += 1
        elif opcode == Opcode.CMP:
            second_val = self.get_operand(instr)
            self.data_path.set_flags(self.data_path.acc - second_val)
            self.latch_instr_ptr(sel_next=True)
            self._tick += 1
        elif opcode == Opcode.JMP:
            self.latch_instr_ptr(False)
            self._tick += 1
        elif opcode == Opcode.JE:
            self.latch_instr_ptr(not self.data_path.is_zero())
            self._tick += 1
        elif opcode == Opcode.HLT:
            raise StopIteration()
        else:
            assert False, "opcode not found!"
        self.data_path.journal.append(str(self))

    def __repr__(self):
        state = f"{{TICK: {self._tick}, PC: {self.instr_ptr}, ADDR: {self.data_path.address_reg}, " \
                f"ACC: {self.data_path.acc}, DR: {self.data_path.data_reg}}}"
        return state


def simulation(data, code, input_tokens, data_memory_size, simulation_limit) -> str:
    data_path = DataPath(data_memory_size, data, input_tokens)
    control_unit = ControlUnit(code, data_path)
    data_path.journal.append('Simulation started')
    instr_counter = 0
    try:
        while True:
            assert simulation_limit > instr_counter, "too long execution, increase simulation_limit!"
            control_unit.decode_and_execute_instr()
            instr_counter += 1
    except StopIteration:
        pass
    except EOFError:
        data_path.journal.append('Input buffer is empty!')
    data_path.journal.append('Simulation finished')
    return f"{os.linesep.join(data_path.journal)}\n" + \
           f"output: '{''.join(data_path.output_buffer)}'\n" \
           f"instructions: {instr_counter}\n" \
           f"ticks: {control_unit.current_tick()}\n" \
           f"memory: {data_path.data_mem}\n" \
           f"acc: {data_path.acc}"
