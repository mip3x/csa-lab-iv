from typing import List, Dict, Any, Tuple

from isa import Opcode, Register
from definitions import *
from ast_nodes import Definition, Vector, StringLiteral, Const, Variable, Alloc
from ast_nodes import Body, Number, Ident, IfStatement, BeginLoop, TimesLoop, String


STDIN_PORT  = 1
STDOUT_PORT = 2

EAX = Register.EAX
EBX = Register.EBX
ECX = Register.ECX
EDX = Register.EDX
EFX = Register.EFX
DR = Register.DR
R10 = Register.r10

ENTRY_LABEL = "__entry_main"

VECTOR_BASE = 0x1


def __mov_imm_to_dst(value: int, dst: Register) -> Dict[str, Any]:
    return {
        "opcode": Opcode.MOV,
        "rd_addr_t": REG_TO_REG_ADDR_T,
        "rs1_addr_t": IMMEDIATE_ADDR_T,
        "rd": dst,
        "imm": int(value),
    }


# mov [reg#1], reg#2
def __mov_reg_to_mem(addr_reg: Register, src_reg: Register) -> Dict[str, Any]:
    return {
        "opcode": Opcode.MOV,
        "rd_addr_t": INDIRECT_ADDR_T,
        "rs1_addr_t": REG_TO_REG_ADDR_T,
        "rd": addr_reg,
        "rs1": src_reg,
    }


# mov reg#1, [reg#2]
def __mov_mem_to_reg(dst_reg: Register, addr_reg: Register) -> Dict[str, Any]:
    return {
        "opcode": Opcode.MOV,
        "rd_addr_t": REG_TO_REG_ADDR_T,
        "rs1_addr_t": INDIRECT_ADDR_T,
        "rd": dst_reg,
        "rs1": addr_reg,
    }


def __push_imm(value: int) -> Dict[str, Any]:
    return {
        "opcode": Opcode.PUSH_DS,
        "rs1_addr_t": IMMEDIATE_ADDR_T,
        "imm": int(value)
    }


def __push_reg(reg: Register) -> Dict[str, Any]:
    return {
        "opcode": Opcode.PUSH_DS,
        "rs1_addr_t": REG_TO_REG_ADDR_T,
        "rs1": reg
    }


def __pop_to_reg(reg: Register) -> Dict[str, Any]:
    return {
        "opcode": Opcode.POP_DS,
        "rd_addr_t": REG_TO_REG_ADDR_T,
        "rd": reg
    }


def __out_port(port: int) -> Dict[str, Any]:
    return {
        "opcode": Opcode.OUT,
        "port": int(port)
    }


def __in_port(port: int) -> Dict[str, Any]:
    return {
        "opcode": Opcode.IN,
        "port": int(port)
    }


#   pop b
#   pop a
#   op a,a,b
#   push a
def __binop_template(opcode: Opcode) -> List[Dict[str, Any]]:
    return [
        __pop_to_reg(EBX),
        __pop_to_reg(EAX),
        {
            "opcode": opcode,
            "rd_addr_t": REG_TO_REG_ADDR_T,
            "rs1_addr_t": REG_TO_REG_ADDR_T,
            "rs2_addr_t": REG_TO_REG_ADDR_T,
            "rd": EAX,
            "rs1": EAX,
            "rs2": EBX
        },
        __push_reg(EAX),
    ]


#   pop a
#   op a,a
#   push a
def __unop_template(opcode: Opcode) -> List[Dict[str, Any]]:
    return [
        __pop_to_reg(EAX),
        {
            "opcode": opcode,
            "rd_addr_t": REG_TO_REG_ADDR_T,
            "rs1_addr_t": REG_TO_REG_ADDR_T,
            "rd": EAX,
            "rs1": EAX
        },
        __push_reg(EAX),
    ]


# get length of instruction in words
def instruction_len(instruction: Dict[str, Any]) -> int:
    opcode = instruction["opcode"]
    if opcode in (Opcode.IN, Opcode.OUT):
        return 1

    if opcode in (Opcode.JMP, Opcode.JCC, Opcode.JCS, Opcode.JEQ, Opcode.JNE,
              Opcode.JLT, Opcode.JGT, Opcode.JLE, Opcode.JGE):
        return 2

    for addressing in (DST_REG_ADDR_T, SRC1_REG_ADDR_T, SRC2_REG_ADDR_T):
        if instruction.get(addressing) in (IMMEDIATE_ADDR_T, INDIRECT_IMM_OFFSET_ADDR_T):
            return 2

    return 1


class DataLayout:
    def __init__(self):
        self.mem: List[int] = []
        self.cursor = 0
        self.symbols: Dict[str, Dict[str, Any]] = {}

    def dump_symbols(self, hex_mode: bool = False) -> None:
        def fmt(n: int) -> str:
            return f"0x{n:04X}" if hex_mode else f"{n:04d}"

        print("DM symbols:")
        for name, meta in self.symbols.items():
            base = meta["addr"]
            size = meta.get("size", 1)
            end  = base + size - 1
            kind = meta["kind"]
            print(f"{fmt(base)}..{fmt(end)} {kind:>5} {name}")

    def add_const(self, name: str, value: int):
        base = self.cursor
        self.mem.append(int(value) & 0xFFFFFFFF)
        self.symbols[name] = {
            "kind": CONST_KIND,
            "addr": base,
            "size": 1,
            "value": int(value)
        }
        self.cursor = len(self.mem)

    def add_var(self, name: str):
        base = self.cursor
        self.mem.append(0)
        self.symbols[name] = {
            "kind": VAR_KIND,
            "addr": base,
            "size": 1
        }
        self.cursor = len(self.mem)

    def add_alloc(self, name: str, size: int):
        size = int(size)
        base = self.cursor
        self.mem.extend([0] * size)
        self.symbols[name] = {
            "kind": ALLOC_KIND,
            "addr": base,
            "size": size
        }
        self.cursor = len(self.mem)

    def add_pstr(self, name: str, string: str):
        base = self.cursor
        self.mem.append(len(string) & 0xFFFFFFFF) # pascal-length

        for char in string:
            self.mem.append(ord(char) & 0xFFFFFFFF)

        self.symbols[name] = {
            "kind": STR_KIND,
            "addr": base,
            "len": len(string),
            "size": 1 + len(string)
        }
        self.cursor = len(self.mem)

    def resolve_addr(self, name: str) -> int:
        if name not in self.symbols:
            raise ValueError(f"символ `{name}` не определён!")
        return self.symbols[name]["addr"]

    def resolve_const_value(self, name: str) -> int:
        if name not in self.symbols or self.symbols[name]["kind"] != CONST_KIND:
            raise ValueError(f"`{name}` не является константой!")
        return int(self.symbols[name]["value"])

    def words(self) -> List[int]:
        return self.mem


class Emitter:
    def __init__(self):
        self.code: List[Dict[str, Any]] = []
        self.labels: Dict[str, int] = {}
        self.patches: List[Dict[str, Any]] = []
        self.pc_words = 0

    def mark(self, label: str):
        self.labels[label] = self.pc_words

    def emit(self, instruction: Dict[str, Any]):
        self.code.append(instruction)
        self.pc_words += instruction_len(instruction)

    def emit_jmp_to_label(self, label: str, opcode: Opcode):
        index = len(self.code)

        instruction = {
            "opcode": opcode,
            "rs1_addr_t": IMMEDIATE_ADDR_T,
            "imm": 0
        }

        self.code.append(instruction)
        self.patches.append(
            {
                "idx": index,
                "label": label,
                "field": IMMEDIATE
            }
        )
        self.pc_words += instruction_len(instruction)

    def patch_all(self):
        for patch in self.patches:
            label = patch["label"]

            if label not in self.labels:
                raise ValueError(f"неизвестная метка: {label}!")

            self.code[patch["idx"]][patch["field"]] = self.labels[label]


#  [ ... a ] ->
#       pop a->A
#       push A
#       push A
#   => [ ... a a ]
def gen_dup(em: Emitter):
    em.emit(__pop_to_reg(EAX))
    em.emit(__push_reg(EAX))
    em.emit(__push_reg(EAX))


#   [ ... b a ] ->
#       pop a->A
#       pop b->B
#       push A
#       push B
#   => [ ... a b ]
def gen_swap(em: Emitter):
    em.emit(__pop_to_reg(EAX))
    em.emit(__pop_to_reg(EBX))
    em.emit(__push_reg(EAX))
    em.emit(__push_reg(EBX))


def gen_drop(em: Emitter):
    em.emit(__pop_to_reg(R10))


# [... b a] -> [... b a b]
def gen_over(em: Emitter):
    em.emit(__pop_to_reg(EAX))
    em.emit(__pop_to_reg(EBX))
    em.emit(__push_reg(EBX))
    em.emit(__push_reg(EAX))
    em.emit(__push_reg(EBX))


# [... a b c] -> [... b c a]
def gen_rot(em: Emitter):
    em.emit(__pop_to_reg(EAX))
    em.emit(__pop_to_reg(EBX))
    em.emit(__pop_to_reg(ECX))
    em.emit(__push_reg(EBX))
    em.emit(__push_reg(EAX))
    em.emit(__push_reg(ECX))


def gen_add(em: Emitter):
    for instruction in __binop_template(Opcode.ADD):
        em.emit(instruction)


def gen_sub(em: Emitter):
    for instruction in __binop_template(Opcode.SUB):
        em.emit(instruction)

    
def gen_mul(em: Emitter):
    for instruction in __binop_template(Opcode.MUL):
        em.emit(instruction)


def gen_div(em: Emitter):
    for instruction in __binop_template(Opcode.DIV):
        em.emit(instruction)


def gen_mod(em: Emitter):
    for instruction in __binop_template(Opcode.MOD):
        em.emit(instruction)


def gen_and(em: Emitter):
    for instruction in __binop_template(Opcode.AND):
        em.emit(instruction)


def gen_or(em: Emitter):
    for instruction in __binop_template(Opcode.OR):
        em.emit(instruction)


def gen_xor(em: Emitter):
    for instruction in __binop_template(Opcode.XOR):
        em.emit(instruction)


def gen_not(em: Emitter):
    for instruction in __unop_template(Opcode.NOT):
        em.emit(instruction)


def gen_neg(em: Emitter):
    for instruction in __unop_template(Opcode.NEG):
        em.emit(instruction)


# (a b) -> bool
def __gen_cmp_bool(em: Emitter, jtrue: Opcode):
    em.emit(__pop_to_reg(EBX))
    em.emit(__pop_to_reg(EAX))

    em.emit(
        {
            "opcode": Opcode.CMP,
            "rs1_addr_t": REG_TO_REG_ADDR_T,
            "rs2_addr_t": REG_TO_REG_ADDR_T,
            "rs1": EAX,
            "rs2": EBX
        }
    )

    L_true = fresh_label("cmp_true")
    L_end = fresh_label("cmp_end")

    em.emit_jmp_to_label(L_true, jtrue)

    em.emit(__push_imm(0))

    em.emit_jmp_to_label(L_end, Opcode.JMP)

    em.mark(L_true)
    em.emit(__push_imm(-1 & 0xFFFFFFFF))

    em.mark(L_end)


def gen_eq(em: Emitter):
    __gen_cmp_bool(em, Opcode.JEQ)


def gen_lt(em: Emitter):
    __gen_cmp_bool(em, Opcode.JLT)


def gen_gt(em: Emitter):
    __gen_cmp_bool(em, Opcode.JGT)


def gen_le(em: Emitter):
    __gen_cmp_bool(em, Opcode.JLE)


def gen_ge(em: Emitter):
    __gen_cmp_bool(em, Opcode.JGE)


def gen_en_int(em: Emitter):
    em.emit({"opcode": Opcode.EN_INT})


def gen_dis_int(em: Emitter):
    em.emit({"opcode": Opcode.DIS_INT})


def gen_iret(em: Emitter):
    em.emit({"opcode": Opcode.IRET})


def gen_exit(em: Emitter):
    em.emit({"opcode": Opcode.HALT})


def gen_print_string(em: Emitter, string: str):
    for char in string:
        em.emit(__mov_imm_to_dst(ord(char), DR))
        em.emit(__out_port(STDOUT_PORT))


# \r\n
def gen_cr(em: Emitter):
    em.emit(__mov_imm_to_dst(CR_CHAR, DR))
    em.emit(__out_port(STDOUT_PORT))

    em.emit(__mov_imm_to_dst(NL_CHAR, DR))
    em.emit(__out_port(STDOUT_PORT))


# procedure call: 
#       push_rs addr(next)
#       jmp label
#
# next_addr = current_pc + length of 2 instructions (push_rs imm (2) + jmp (2) = 4)
def gen_call(em: Emitter, label: str):
    next_addr = em.pc_words + 4

    em.emit(
        {"opcode": Opcode.PUSH_RS,
         "rs1_addr_t": IMMEDIATE_ADDR_T,
         "imm": next_addr
        }
    )
    em.emit_jmp_to_label(label, Opcode.JMP)


_label_counter = 0
def fresh_label(prefix: str) -> str:
    global _label_counter
    _label_counter += 1
    return f"{prefix}_{_label_counter}"


def compile_program(ast) -> Tuple[List[Dict[str, Any]], List[int]]:
    dm = DataLayout()
    em = Emitter()

    em.emit_jmp_to_label(ENTRY_LABEL, Opcode.JMP)

    vectors: Dict[int, str] = {}
    procedure_bodies: Dict[str, Any] = {}

    # consts
    for binding in ast.bindings:
        if isinstance(binding, Const):
            if not isinstance(binding.number, Number):
                raise ValueError(f"const {binding.ident.value} должен иметь числовое значение!")
            dm.add_const(binding.ident.value, binding.number.value)

    # str_lits
    for binding in ast.bindings:
        if isinstance(binding, StringLiteral):
            string = binding.string.value
            dm.add_pstr(binding.ident.value, string)

    # vars
    for binding in ast.bindings:
        if isinstance(binding, Variable):
            dm.add_var(binding.ident.value)

    # allocs
    for binding in ast.bindings:
        if isinstance(binding, Alloc):
            size = None
            if isinstance(binding.number, Number):
                size = binding.number.value
            elif isinstance(binding.number, Const):
                if (binding.number.number is not None) and isinstance(binding.number.number, Number):
                    size = binding.number.number.value
                else:
                    size = dm.resolve_const_value(binding.number.ident.value)
            else:
                raise ValueError(f"alloc {binding.ident.value} требует число или const!")
            dm.add_alloc(binding.ident.value, size)

    # procedures/vectors
    procedure_bodies: Dict[str, Any] = {}
    for binding in ast.bindings:
        if isinstance(binding, Definition):
            procedure_bodies[binding.ident.value] = binding.body

        elif isinstance(binding, Vector):
            if isinstance(binding.port, Number):
                port_val = int(binding.port.value)
            elif isinstance(binding.port, Const):
                if (binding.port.number is not None) and isinstance(binding.port.number, Number):
                    port_val = int(binding.port.number.value)
                else:
                    port_val = int(dm.resolve_const_value(binding.port.ident.value))
            else:
                raise ValueError("vector <num|const> : <handler> — неверный тип порта!")

            if port_val in vectors:
                raise ValueError(f"повторное определение обработчика порта {port_val}!")
            vectors[port_val] = binding.ident.value

    # vectors table
    while em.pc_words < VECTOR_BASE:
        em.emit(
            {"opcode": Opcode.NOP}
        )

    for port, handler in sorted(vectors.items()):
        while em.pc_words < VECTOR_BASE + port:
            em.emit(
                {"opcode": Opcode.NOP}
            )
        em.emit_jmp_to_label(handler, Opcode.JMP)

    # 2nd traverse: generating code for procedures (`ret` in the end)
    for name, body in procedure_bodies.items():
        em.mark(name)
        gen_body(em, body, procedure_bodies, dm)
        em.emit(
            {"opcode": Opcode.RET}
        )

    # 3) top-level body
    em.mark(ENTRY_LABEL)
    gen_body(em, ast.body, procedure_bodies, dm)
    em.emit(
        {"opcode": Opcode.HALT}
    )

    # 4) patching
    em.patch_all()

    dm.dump_symbols(hex_mode=True)
    return em.code, dm.words()


def gen_body(em: Emitter, body, procedure_map, dm : DataLayout):
    assert isinstance(body, Body)

    i = 0
    statements = body.statements

    while i < len(statements):
        statement = statements[i]

        if isinstance(statement, Number):
            em.emit(__push_imm(statement.value))
            i += 1
            continue

        if isinstance(statement, String):
            string = statement.value
            gen_print_string(em, string)
            i += 1
            continue

        #   pop -> A
        #   cmp A, #0
        #   jeq L_end
        #       <ifbody>;
        #       [else? <elsebody>];
        #   L_end
        if isinstance(statement, IfStatement):
            em.emit(__pop_to_reg(EAX))
            em.emit(
                {
                    "opcode": Opcode.CMP,
                    "rs1_addr_t": REG_TO_REG_ADDR_T,
                    "rs2_addr_t": IMMEDIATE_ADDR_T,
                    "rs1": EAX,
                    "imm": 0
                }
            )

            L_else = fresh_label("if_else")
            L_end  = fresh_label("if_end")

            if statement.elsebody is not None:
                em.emit_jmp_to_label(L_else, Opcode.JEQ)
                gen_body(em, statement.ifbody, procedure_map, dm)
                em.emit_jmp_to_label(L_end, Opcode.JMP)
                em.mark(L_else)
                gen_body(em, statement.elsebody, procedure_map, dm)
                em.mark(L_end)
            else:
                em.emit_jmp_to_label(L_end, Opcode.JEQ)
                gen_body(em, statement.ifbody, procedure_map, dm)
                em.mark(L_end)

            i += 1
            continue

        if isinstance(statement, BeginLoop):
            L_loop = fresh_label("begin_loop")
            em.mark(L_loop)

            gen_body(em, statement.body, procedure_map, dm)
            em.emit(__pop_to_reg(EAX))
            em.emit(
                {
                    "opcode": Opcode.CMP,
                    "rs1_addr_t": REG_TO_REG_ADDR_T,
                    "rs2_addr_t": IMMEDIATE_ADDR_T,
                    "rs1": EAX,
                    "imm": 0
                }
            )
            em.emit_jmp_to_label(L_loop, Opcode.JEQ)

            i += 1
            continue

        #   pop n->C
        #   push_rs C
        #       L: <body>
        #   pop_rs C
        #   sub C,#1
        #   push_rs C
        #   cmp C,#0
        #   jgt L
        #   pop_rs C
        if isinstance(statement, TimesLoop):
            L_loop = fresh_label("times_loop")
            em.emit(__pop_to_reg(ECX))

            em.emit(
                {
                    "opcode": Opcode.PUSH_RS,
                    "rs1_addr_t": REG_TO_REG_ADDR_T,
                    "rs1": ECX
                }
            )
            em.mark(L_loop)

            gen_body(em, statement.body, procedure_map, dm)

            em.emit(
                {
                    "opcode": Opcode.POP_RS,
                    "rd_addr_t": REG_TO_REG_ADDR_T,
                    "rd": ECX
                }
            )
            em.emit(
                {
                    "opcode": Opcode.SUB,
                    "rd_addr_t": REG_TO_REG_ADDR_T,
                    "rs1_addr_t": REG_TO_REG_ADDR_T,
                    "rs2_addr_t": IMMEDIATE_ADDR_T,
                    "rd": ECX,
                    "rs1": ECX,
                    "imm": 1
                }
            )
            em.emit(
                {
                    "opcode": Opcode.PUSH_RS,
                    "rs1_addr_t": REG_TO_REG_ADDR_T,
                    "rs1": ECX
                }
            )
            em.emit(
                {
                    "opcode": Opcode.CMP,
                    "rs1_addr_t": REG_TO_REG_ADDR_T,
                    "rs2_addr_t": IMMEDIATE_ADDR_T,
                    "rs1": ECX,
                    "imm": 0
                }
            )

            em.emit_jmp_to_label(L_loop, Opcode.JGT)
            em.emit(
                {
                    "opcode": Opcode.POP_RS,
                    "rd_addr_t": REG_TO_REG_ADDR_T,
                    "rd": ECX
                }
            )

            i += 1
            continue

        if isinstance(statement, Ident):
            word = statement.value

            if word == PRINT_STRING_SYM:
                if i + 1 >= len(statements):
                    raise ValueError(f'после ." ожидается строка!')

                next = statements[i + 1]
                if isinstance(next, String):
                    string = next.value
                elif isinstance(next, Ident):
                    string = next.value
                else:
                    raise ValueError(f'после ." ожидается строка, но встречено: {next}!')

                gen_print_string(em, string)
                i += 2
                continue

            if word == DOT_SYM:
                em.emit(__pop_to_reg(DR))
                em.emit(__out_port(STDOUT_PORT))
                i += 1
                continue

            if word == "emit":
                em.emit(__pop_to_reg(DR))
                em.emit(__out_port(STDOUT_PORT))
                i += 1
                continue

            if word == "key":
                em.emit(__in_port(STDIN_PORT))
                em.emit(__push_reg(DR))
                i += 1
                continue

            if word == "cr":
                gen_cr(em)
                i += 1
                continue

            if word == "dup":
                gen_dup(em)
                i += 1
                continue

            if word == "swap":
                gen_swap(em)
                i += 1
                continue

            if word == "drop":
                gen_drop(em)
                i += 1
                continue

            if word == "over":
                gen_over(em)
                i += 1
                continue

            if word == "rot":
                gen_rot(em)
                i += 1
                continue

            # [... b a] -> [... a]
            if word == "nip":
                em.emit(__pop_to_reg(EAX))
                em.emit(__pop_to_reg(EBX))
                em.emit(__push_reg(EAX))
                i += 1
                continue

            if word == ">r":
                em.emit(__pop_to_reg(EFX))
                em.emit(
                    {
                        "opcode": Opcode.PUSH_RS,
                        "rs1_addr_t": REG_TO_REG_ADDR_T,
                        "rs1": EFX
                    }
                )
                i += 1
                continue

            if word == "r>":
                em.emit(
                    {
                        "opcode": Opcode.POP_RS,
                        "rd_addr_t": REG_TO_REG_ADDR_T,
                        "rd": EFX
                    }
                )
                em.emit(__push_reg(EFX))
                i += 1
                continue

            # peek: pop_rs (EFX) -> push_rs (EFX) -> push_ds (EFX)
            if word == "r@":
                em.emit(
                    {
                        "opcode": Opcode.POP_RS,
                        "rd_addr_t": REG_TO_REG_ADDR_T,
                        "rd": EFX
                    }
                )
                em.emit(
                    {
                        "opcode": Opcode.PUSH_RS,
                        "rs1_addr_t": REG_TO_REG_ADDR_T,
                        "rs1": EFX
                    }
                )
                em.emit(__push_reg(EFX))
                i += 1
                continue

            if word == "@":
                em.emit(__pop_to_reg(EDX))
                em.emit(__mov_mem_to_reg(EAX, EDX))
                em.emit(__push_reg(EAX))
                i += 1
                continue

            if word == "!":
                em.emit(__pop_to_reg(EAX)) # value
                em.emit(__pop_to_reg(EDX)) # addr
                em.emit(__mov_reg_to_mem(EDX, EAX))
                i += 1
                continue

            if word == "+":
                gen_add(em)
                i += 1
                continue

            if word == "-":
                gen_sub(em)
                i += 1
                continue

            if word == "*":
                gen_mul(em)
                i += 1
                continue

            if word == "/":
                gen_div(em)
                i += 1
                continue

            if word == "mod":
                gen_mod(em)
                i += 1
                continue

            if word == "and":
                gen_and(em)
                i += 1
                continue

            if word == "or":
                gen_or(em)
                i += 1
                continue

            if word == "not":
                gen_not(em)
                i += 1
                continue

            if word == "neg":
                gen_neg(em)
                i += 1
                continue

            if word == "=":
                gen_eq(em)
                i += 1
                continue

            if word == "<":
                gen_lt(em)
                i += 1
                continue

            if word == ">":
                gen_gt(em)
                i += 1
                continue

            if word == "<=":
                gen_le(em)
                i += 1
                continue

            if word == ">=":
                gen_ge(em)
                i += 1
                continue

            if word == "_enable_int_":
                gen_en_int(em)
                i += 1
                continue

            if word == "_disable_int_":
                gen_dis_int(em)
                i += 1
                continue

            if word == "_iret_":
                gen_iret(em)
                i += 1
                continue

            if word == "_exit_":
                gen_exit(em)
                i += 1
                continue

            if word in procedure_map:
                gen_call(em, word)
                i += 1
                continue

            sym = dm.symbols.get(word)
            if sym:
                if sym["kind"] == CONST_KIND:
                    # const -> put
                    em.emit(__push_imm(sym["value"]))
                else:
                    # var/str/alloc -> put addr on stack
                    em.emit(__push_imm(sym["addr"]))
                i += 1
                continue

            raise ValueError(f"неизвестное слово: {word}!")

        raise ValueError(f"необработанный узел AST в gen_body: {statement}!")