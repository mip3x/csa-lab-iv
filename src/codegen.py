from typing import List, Dict, Any, Tuple

from isa import Opcode, Register
from definitions import *
from ast_nodes import Definition, Vector, StringLiteral, Const, Variable, Alloc
from ast_nodes import Body, Number, Ident, IfStatement, TimesLoop, String


STDIN_PORT  = 1
STDOUT_PORT = 2

EAX = Register.EAX
EBX = Register.EBX
ECX = Register.ECX
DR = Register.DR

ENTRY_LABEL = "__entry_main"


def __mov_imm_to_dst(value: int, dst: Register) -> Dict[str, Any]:
    return {
        "opcode": Opcode.MOV,
        "rd_addr_t": REG_TO_REG_ADDR_T,
        "rs1_addr_t": IMMEDIATE_ADDR_T,
        "rd": dst,
        "imm": int(value),
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


def gen_add(em: Emitter):
    for instruction in __binop_template(Opcode.ADD):
        em.emit(instruction)


def gen_mod(em: Emitter):
    for instruction in __binop_template(Opcode.MOD):
        em.emit(instruction)


def gen_or(em: Emitter):
    for instruction in __binop_template(Opcode.OR):
        em.emit(instruction)


def gen_not(em: Emitter):
    for instruction in __unop_template(Opcode.NOT):
        em.emit(instruction)


# compare two top values: (a b -- bool)
#   pop b->B
#   pop a->A
#   cmp A,B
#   if equal ->
#       push -1
#   else
#       push 0
def gen_eq(em: Emitter):
    em.emit(__pop_to_reg(EBX))
    em.emit(__pop_to_reg(EAX))

    em.emit(
        {"opcode": Opcode.CMP,
         "rs1_addr_t": REG_TO_REG_ADDR_T,
         "rs2_addr_t": REG_TO_REG_ADDR_T,
         "rs1": EAX,
         "rs2": EBX
        }
    )

    L_true = fresh_label("eq_true")
    L_end  = fresh_label("eq_end")

    em.emit_jmp_to_label(L_true, Opcode.JEQ)
    em.emit(__push_imm(0))

    em.emit_jmp_to_label(L_end, Opcode.JMP)

    em.mark(L_true)
    em.emit(__push_imm(-1 & 0xFFFFFFFF))
    em.mark(L_end)


def gen_print_string(em: Emitter, string: str):
    for char in string:
        em.emit(__mov_imm_to_dst(ord(char), DR))
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

    # 1st traverse: collect list of procedures (definition) and give labels
    procedure_bodies: Dict[str, Any] = {}
    for binding in ast.bindings:
        if isinstance(binding, Definition):
            procedure_bodies[binding.ident.value] = binding.body

    # 2nd traverse: generating code for procedures (`ret` in the end)
    for name, body in procedure_bodies.items():
        em.mark(name)
        gen_body(em, body, procedure_bodies)
        em.emit(
            {"opcode": Opcode.RET}
        )

    # 3) top-level body
    em.mark(ENTRY_LABEL)
    gen_body(em, ast.body, procedure_bodies)
    em.emit(
        {"opcode": Opcode.HALT}
    )

    # 4) patching
    em.patch_all()

    return em.code, dm.words()


def gen_body(em: Emitter, body, procedure_map):
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
                gen_body(em, statement.ifbody, procedure_map)
                em.emit_jmp_to_label(L_end, Opcode.JMP)
                em.mark(L_else)
                gen_body(em, statement.elsebody, procedure_map)
                em.mark(L_end)
            else:
                em.emit_jmp_to_label(L_end, Opcode.JEQ)
                gen_body(em, statement.ifbody, procedure_map)
                em.mark(L_end)

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

            gen_body(em, statement.body, procedure_map)

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

            if word == "dup":
                gen_dup(em)
                i += 1
                continue

            if word == "swap":
                gen_swap(em)
                i += 1
                continue

            if word == "+":
                gen_add(em)
                i += 1
                continue

            if word == "mod":
                gen_mod(em)
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

            if word == "=":
                gen_eq(em)
                i += 1
                continue

            if word in procedure_map:
                gen_call(em, word)
                i += 1
                continue

            raise ValueError(f"неизвестное слово: {word}!")

        raise ValueError(f"необработанный узел AST в gen_body: {statement}!")