import json

from enum import Enum


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

binary_to_opcode = {
    0x0: Opcode.HALT,
    0x1: Opcode.PUSH_DS,
    0x2: Opcode.POP_DS,
    0x3: Opcode.ADD,
    0x4: Opcode.ADC,
    0x5: Opcode.SUB,
    0x6: Opcode.MUL,
    0x7: Opcode.DIV,
    0x8: Opcode.MOD,
    0x9: Opcode.NEG,
    0x0A: Opcode.CMP,
    0x0B: Opcode.AND,
    0x0C: Opcode.OR,
    0x0D: Opcode.XOR,
    0x0E: Opcode.NOT,
    0x0F: Opcode.JMP,
    0x10: Opcode.JCC,
    0x11: Opcode.JCS,
    0x12: Opcode.JEQ,
    0x13: Opcode.JNE,
    0x14: Opcode.JLT,
    0x15: Opcode.JGT,
    0x16: Opcode.JLE,
    0x17: Opcode.JGE,
    0x18: Opcode.MOV,
    0x19: Opcode.NOP,
    0x1A: Opcode.OUT,
    0x1B: Opcode.IN,
    0x1C: Opcode.EN_INT,
    0x1D: Opcode.DIS_INT,
    0x1E: Opcode.IRET,
    0x1F: Opcode.PUSH_RS,
    0x20: Opcode.POP_RS,
    0x21: Opcode.RET
}


def to_bytes(code):
    
    binary_bytes = bytearray()
    for instr in code:
        # Получаем бинарный код операции
        opcode_bin = opcode_to_binary[instr["opcode"]] << 28

        # Добавляем адрес перехода, если он есть
        arg = instr.get("arg", 0)

        # Формируем 32-битное слово: опкод (4 бита) + адрес (28 бит)
        binary_instr = opcode_bin | (arg & 0x0FFFFFFF)

        # Преобразуем 32-битное целое число в 4 байта (big-endian)
        binary_bytes.extend(
            ((binary_instr >> 24) & 0xFF, (binary_instr >> 16) & 0xFF, (binary_instr >> 8) & 0xFF, binary_instr & 0xFF)
        )

    return bytes(binary_bytes)


def to_hex(code):
    """Преобразует машинный код в текстовый файл с шестнадцатеричным представлением.

    Формат вывода:
    <address> - <HEXCODE> - <mnemonic>
    Например:
    20 - 03340301 - add #01 <- 34 + #03
    """
    binary_code = to_bytes(code)
    result = []

    for i in range(0, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break

        # Формируем 32-битное слово из 4 байтов
        word = (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]

        # Получаем опкод и адрес
        opcode_bin = (word >> 28) & 0xF
        arg = word & 0x0FFFFFFF

        # Преобразуем опкод и адрес в мнемонику
        mnemonic = binary_to_opcode[opcode_bin].value
        if opcode_bin in (0x6, 0x7):  # jmp или jz требуют аргумент
            mnemonic = f"{mnemonic} {arg}"

        # Формируем строку в требуемом формате
        hex_word = f"{word:08X}"
        address = i // 4
        line = f"{address} - {hex_word} - {mnemonic}"
        result.append(line)

    return "\n".join(result)


def from_bytes(binary_code):
    """Преобразует бинарное представление машинного кода в структурированный формат.

    Бинарное представление инструкций:

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 31...28 │ 27                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      адрес перехода                         │
    └─────────┴─────────────────────────────────────────────────────────────┘
    """
    structured_code = []
    # Обрабатываем байты по 4 за раз для получения 32-битных инструкций
    for i in range(0, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break

        # Формируем 32-битное слово из 4 байтов
        binary_instr = (
            (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]
        )

        # Извлекаем опкод (старшие 4 бита)
        opcode_bin = (binary_instr >> 28) & 0xF
        opcode = binary_to_opcode[opcode_bin]

        # Извлекаем адрес перехода (младшие 28 бит)
        arg = binary_instr & 0x0FFFFFFF

        # Формируем структуру инструкции
        instr = {"index": i // 4, "opcode": opcode}

        # Добавляем адрес перехода только для инструкций перехода
        # if opcode in (Opcode.JMP, Opcode.JZ):
        #     instr["arg"] = arg

        structured_code.append(instr)

    return structured_code


def write_json(filename, code):
    """Записать машинный код в JSON файл.

    - Список JSON. Один элемент списка -- одна инструкция.
    - Индекс списка соответствует:
         - адресу оператора в исходном коде;
         - адресу инструкции в машинном коде.

    Пример:

    ```json
    [
        { "index": 0, "opcode": "jz", "arg": 5, "term": [ 1, 5, "]" ] },
    ]
    ```

    где:

    - `index` -- номер в машинном коде, необходим для того, чтобы понимать, куда делается условный переход;
    - `opcode` -- строка с кодом операции (тип: `Opcode`);
    - `arg` -- аргумент инструкции (если требуется);
    - `term` -- информация о связанном месте в исходном коде (если есть).
    """
    with open(filename, "w", encoding="utf-8") as file:
        # Почему не: `file.write(json.dumps(code, indent=4))`?
        # Чтобы одна инструкция была на одну строку.
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")
