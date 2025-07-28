from enum import Enum
from definitions import *


class Opcode(str, Enum):
    MOV = "mov"
    PUSH_DS = "push_ds"
    POP_DS = "pop_ds"
    PUSH_RS = "push_rs"
    POP_RS = "pop_rs"
    RET = "ret"

    ADD = "add"
    ADC = "adc"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    NEG = "neg"
    CMP = "cmp"

    AND = "and"
    OR = "or"
    XOR = "xor"
    NOT = "not"

    JMP = "jmp"
    JCC = "jcc"
    JCS = "jcs"
    JEQ = "jeq"
    JNE = "jne"
    JLT = "jlt"
    JGT = "jgt"
    JLE = "jle"
    JGE = "jge"

    HALT = "halt"
    NOP = "nop"

    OUT = "out"
    IN = "in"

    EN_INT = "en_int"
    DIS_INT = "dis_int"
    IRET = "iret"

    def __str__(self):
        return str(self.value)


opcode_to_binary = {
    Opcode.HALT: 0x0,
    Opcode.PUSH_DS: 0x1,
    Opcode.POP_DS: 0x2,
    Opcode.ADD: 0x3,
    Opcode.ADC: 0x4,
    Opcode.SUB: 0x5,
    Opcode.MUL: 0x6,
    Opcode.DIV: 0x7,
    Opcode.MOD: 0x8,
    Opcode.NEG: 0x9,
    Opcode.CMP: 0x0A,
    Opcode.AND: 0x0B,
    Opcode.OR: 0x0C,
    Opcode.XOR: 0x0D,
    Opcode.NOT: 0x0E,
    Opcode.JMP: 0x0F,
    Opcode.JCC: 0x10,
    Opcode.JCS: 0x11,
    Opcode.JEQ: 0x12,
    Opcode.JNE: 0x13,
    Opcode.JLT: 0x14,
    Opcode.JGT: 0x15,
    Opcode.JLE: 0x16,
    Opcode.JGE: 0x17,
    Opcode.MOV: 0x18,
    Opcode.NOP: 0x19,
    Opcode.OUT: 0x1A,
    Opcode.IN: 0x1B,
    Opcode.EN_INT: 0x1C,
    Opcode.DIS_INT: 0x1D,
    Opcode.IRET: 0x1E,
    Opcode.PUSH_RS: 0x1F,
    Opcode.POP_RS: 0x20,
    Opcode.RET: 0x21
}

binary_to_opcode = {v: k for k, v in opcode_to_binary.items()}


def __opcode_uses_rd(opcode : Opcode) -> bool:
    return opcode in {
        Opcode.MOV, Opcode.ADD, Opcode.ADC, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD,
        Opcode.AND, Opcode.OR, Opcode.XOR, Opcode.NEG, Opcode.NOT,
        Opcode.POP_DS, Opcode.POP_RS
    }


def __opcode_uses_rs1(opcode : Opcode) -> bool:
    return opcode in {
        Opcode.MOV, Opcode.ADD, Opcode.ADC, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD,
        Opcode.AND, Opcode.OR, Opcode.XOR, Opcode.CMP, Opcode.NEG, Opcode.NOT,
        Opcode.PUSH_DS, Opcode.PUSH_RS
    }


def __opcode_uses_rs2(opcode : Opcode) -> bool:
    return opcode in {
        Opcode.ADD, Opcode.ADC, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD,
        Opcode.AND, Opcode.OR, Opcode.XOR, Opcode.CMP
    }


class Register(str, Enum):
    EAX = "EAX"
    EBX = "EBX"
    ECX = "ECX"
    EDX = "EDX"
    EFX = "EFX"
    r6  = "r6"
    r7  = "r7"
    r8  = "r8"
    r9  = "r9"
    r10 = "r10"
    PC  = "PC"
    AR  = "AR"
    DR  = "DR"
    SP  = "SP"
    RP  = "RP"
    IR = "IR"

    def __str__(self):
        return self.value


register_to_id = {
    Register.EAX: 0, Register.EBX: 1, Register.ECX: 2,
    Register.EDX: 3, Register.EFX: 4, Register.r6: 5,
    Register.r7: 6,  Register.r8: 7, Register.r9: 8,
    Register.r10: 9, Register.PC: 10, Register.AR: 11,
    Register.DR: 12, Register.SP: 13, Register.RP: 14,
    Register.IR: 15,
}

id_to_register = {v: k for k, v in register_to_id.items()}


def __get_reg_id(reg: Register) -> int:
    if reg is None:
        return 0
    if isinstance(reg, int):
        return reg & 0xF
    return register_to_id[reg]


def __get_reg_name_by_id(id: int) -> str:
    return id_to_register.get(id, f"reg?_{id}")


addr_kind = {
    "reg": 0b00,
    "imm": 0b01,
    "ind": 0b10,
    "ind+imm": 0b11,
}

addr_kind_rev = {v: k for k, v in addr_kind.items()}


def __get_addr_t_id(addr_t_name: str) -> int:
    if addr_t_name is None:
        return addr_kind[REG_TO_REG_ADDR_T]
    return addr_kind[addr_t_name]


def __pack_addr_t(rd_addr_t, rs1_addr_t, rs2_addr_t):
    return ((rd_addr_t & 0b11) << 0) | ((rs1_addr_t & 0b11) << 2) | ((rs2_addr_t & 0b11) << 4)


JUMP_OPS = {
    Opcode.JMP, Opcode.JCC, Opcode.JCS, Opcode.JEQ, Opcode.JNE,
    Opcode.JLT, Opcode.JGT, Opcode.JLE, Opcode.JGE
}


def __format_operand(addr_t_kind_bits: int, reg_id: int, immediate: int = None) -> str:
    if addr_t_kind_bits == addr_kind[REG_TO_REG_ADDR_T]:
        return __get_reg_name_by_id(reg_id)

    if addr_t_kind_bits == addr_kind[IMMEDIATE_ADDR_T]:
        return f"#{immediate if immediate is not None else 0}"

    if addr_t_kind_bits == addr_kind[INDIRECT_ADDR_T]:
        return f"[{__get_reg_name_by_id(reg_id)}]"

    if addr_t_kind_bits == addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]:
        return f"[{__get_reg_name_by_id(reg_id)}+{immediate if immediate is not None else 0}]"

    return __get_reg_name_by_id(reg_id)


def __pack_machine_word(opcode_bin, addr_t_bin, rd, rs1, rs2):
    """
    ┌───────────┬──────────┬───────────┬──────────┬───────────┬──────────┐
    │  31..24   │  23..20  │  19..16   │  15..12  │   11..6   │   5..0   │              
    ├───────────┼──────────┼───────────┼──────────┼───────────┼──────────┤
    │    0x0    │    rs2   │    rs1    │    rd    │   addr_t  │  opcode  │         
    └───────────┴──────────┴───────────┴──────────┴───────────┴──────────┘
    """
    word = 0
    word |= (rs2 & 0xF) << 20
    word |= (rs1 & 0xF) << 16
    word |= (rd & 0xF) << 12
    word |= (addr_t_bin & 0x3F) << 6
    word |= (opcode_bin & 0x3F)
    
    return word


def to_bytes(code):
    binary_bytes = bytearray()

    for instr in code:
        opcode : Opcode = instr["opcode"]
        opcode_bin = opcode_to_binary[opcode] & 0x3F

        if opcode in (Opcode.IN, Opcode.OUT):
            if PORT not in instr:
                raise ValueError(f"для {opcode} требуется поле `port`!")
            port = int(instr[PORT]) & 0x3FF

            word = 0
            word |= (port << 6)
            word |= opcode_bin

            # big-endian
            binary_bytes.extend(
                (
                    (word >> 24) & 0xFF,
                    (word >> 16) & 0xFF,
                    (word >> 8) & 0xFF,
                    word & 0xFF
                )
            )

            continue

        # get registers id
        rd = __get_reg_id(instr.get(DST_REG))
        rs1 = __get_reg_id(instr.get(SRC1_REG))
        rs2 = __get_reg_id(instr.get(SRC2_REG))

        # get addr_t id
        rd_addr_t = __get_addr_t_id(instr.get(DST_REG_ADDR_T))
        rs1_addr_t = __get_addr_t_id(instr.get(SRC1_REG_ADDR_T))
        rs2_addr_t = __get_addr_t_id(instr.get(SRC2_REG_ADDR_T))
        addr_t_bin = __pack_addr_t(rd_addr_t=rd_addr_t, rs1_addr_t=rs1_addr_t, rs2_addr_t=rs2_addr_t)

        # immediate value field
        immediate_value = None
        if IMMEDIATE in instr:
            immediate_value = int(instr[IMMEDIATE])
        elif ADDRESS in instr:
            immediate_value = int(instr[ADDRESS])
        elif ARGUMENT in instr:
            immediate_value = int(instr[ARGUMENT])

        # emitting 1st word
        word = __pack_machine_word(opcode_bin, addr_t_bin, rd, rs1, rs2)
        binary_bytes.extend(
                (
                    (word >> 24) & 0xFF,
                    (word >> 16) & 0xFF,
                    (word >> 8) & 0xFF,
                    word & 0xFF
                )
            )

        needs_immediate = (
            rd_addr_t  in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            rs1_addr_t in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            rs2_addr_t in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            opcode in JUMP_OPS
        )

        if needs_immediate:
            if immediate_value is None:
                raise ValueError(f"для {opcode} требуется `immediate/port/addr`, но он не задан: {instr}!")
            immediate_word = immediate_value & 0xFFFFFFFF
            binary_bytes.extend(
                (
                    (immediate_word >> 24) & 0xFF,
                    (immediate_word >> 16) & 0xFF,
                    (immediate_word >> 8) & 0xFF,
                    immediate_word & 0xFF)
            )

    return bytes(binary_bytes)


def to_hex(code):
    """Преобразует машинный код в текстовый файл с шестнадцатеричным представлением.

    Формат вывода:
    <address> - <HEXCODE> - <mnemonic>
    Например:
    0 - 00010018 - mov EAX, EBX
    1 - 00002118 - mov ECX, #123456
    2 - 0001E240 - imm=123456
    3 - 00010098 - mov [EAX], EBX
    4 - 00010318 - mov EAX, [EBX+4]
    5 - 00000004 - imm=4
    6 - 0000000F - jmp
    7 - 00000064 - imm=100
    8 - 0000009A - out port=2
    9 - 000001DB - in port=7
    10 - 00000021 - ret
    """
    binary_code = to_bytes(code)
    result = []
    i = 0

    while i < len(binary_code):
        if i + 3 >= len(binary_code):
            break

        word = (
            (binary_code[i] << 24)
            | (binary_code[i + 1] << 16)
            | (binary_code[i + 2] << 8)
            | binary_code[i + 3]
        )

        opcode_bin = word & 0x3F
        addr_t = (word >> 6) & 0x3F
        rd = (word >> 12) & 0xF
        rs1 = (word >> 16) & 0xF
        rs2 = (word >> 20) & 0xF

        opcode = binary_to_opcode.get(opcode_bin, None)
        if opcode:
            mnemonic = opcode.value
        else:
            mnemonic = f"unk?_{opcode_bin:02X}"
        
        address = i // 4
        hex_word = f"{word:08X}"

        if opcode in (Opcode.IN, Opcode.OUT):
            port = (word >> 6) & 0x3FF
            line = f"{address} - {hex_word} - {mnemonic} port={port}"
            result.append(line)
            i += 4
            continue

        rd_addr_t  = (addr_t >> 0) & 0b11
        rs1_addr_t = (addr_t >> 2) & 0b11
        rs2_addr_t = (addr_t >> 4) & 0b11

        needs_immediate = (
            rd_addr_t  in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            rs1_addr_t in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            rs2_addr_t in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            opcode in JUMP_OPS
        )

        immediate = None
        if needs_immediate:
            if i + 7 >= len(binary_code):
                pass
            else:
                immediate = (
                    (binary_code[i + 4] << 24)
                    | (binary_code[i + 5] << 16)
                    | (binary_code[i + 6] << 8)
                    | binary_code[i + 7]
                )

        

        operands = []
        if __opcode_uses_rd(opcode):
            operands.append(__format_operand(rd_addr_t, rd, immediate))

        if __opcode_uses_rs1(opcode):
            operands.append(__format_operand(rs1_addr_t, rs1, immediate))

        if __opcode_uses_rs2(opcode):
            operands.append(__format_operand(rs2_addr_t, rs2, immediate))

        if operands:
            mnemonic_to_print = f"{mnemonic} " + ", ".join(operands)
        else:
            mnemonic_to_print = mnemonic

        result.append(f"{address} - {hex_word} - {mnemonic_to_print}")
        i += 4

        if needs_immediate and immediate is not None:
            result.append(f"{i // 4} - {immediate:08X} - imm={immediate}")
            i += 4

    return "\n".join(result)


def from_bytes(binary_code):
    structured_code = []
    i = 0
    instr_index = 0 # instruction index in words

    while i < len(binary_code):
        if i + 3 >= len(binary_code):
            break

        binary_instr = (
            (binary_code[i] << 24)
            | (binary_code[i + 1] << 16)
            | (binary_code[i + 2] << 8)
            | binary_code[i + 3]
        )
        i += 4

        opcode_bin = binary_instr & 0x3F
        opcode = binary_to_opcode.get(opcode_bin, Opcode.NOP)

        if opcode in (Opcode.IN, Opcode.OUT):
            port = (binary_instr >> 6) & 0x3FF
            structured_code.append(
                {"index": instr_index, "opcode": opcode, "port": port}
            )
            instr_index += 1
            continue

        # getting addr_t and registers
        addr_t = (binary_instr >> 6) & 0x3F
        rd = (binary_instr >> 12) & 0xF
        rs1 = (binary_instr >> 16) & 0xF
        rs2 = (binary_instr >> 20) & 0xF

        # get addr_t for each register
        rd_addr_t = (addr_t >> 0) & 0b11
        rs1_addr_t = (addr_t >> 2) & 0b11
        rs2_addr_t = (addr_t >> 4) & 0b11

        instr = {
            "index": instr_index,
            "opcode": opcode,
            DST_REG: rd,
            SRC1_REG: rs1,
            SRC2_REG: rs2,
            DST_REG_ADDR_T: rd_addr_t,
            SRC1_REG_ADDR_T: rs1_addr_t,
            SRC2_REG_ADDR_T: rs2_addr_t
        }

        needs_immediate = (
            rd_addr_t  in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            rs1_addr_t in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            rs2_addr_t in (addr_kind[IMMEDIATE_ADDR_T], addr_kind[INDIRECT_IMM_OFFSET_ADDR_T]) or
            opcode in JUMP_OPS
        )

        if needs_immediate:
            if i + 3 >= len(binary_code):
                raise ValueError(f"ожидался immediate для {opcode}, но достигнут EOF!")

            imm = (
                (binary_code[i] << 24)
                | (binary_code[i + 1] << 16)
                | (binary_code[i + 2] << 8)
                | (binary_code[i + 3])
            )
            i += 4
            instr[IMMEDIATE] = imm
            instr_index += 2
        else:
            instr_index += 1

        structured_code.append(instr)

    return structured_code