#!/usr/bin/python3

import os
import sys
from enum import Enum
from typing import List

from definitions import *


class Keyword(str, Enum):
    DEF_START = ":"
    DEF_END = ";"
    IF = "if"
    THEN = "then"
    BEGIN = "begin"
    UNTIL = "until"
    TIMES = "times"
    NEXT = "next"
    VAR = "var"
    CONST = "const"
    STR = "str"
    ALLOC = "alloc"
    VECTOR = "vector"


class TokenType(str, Enum):
    NUMBER = "NUMBER"
    STRING = "STRING"
    WORD = "WORD"
    SYM = "SYM"


class Token:
    def __init__(self, kind: TokenType, value: str):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f"Token({self.kind}, {self.value})"


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = list()
    i = 0
    source_len = len(source)
    
    while i < source_len:
        char = source[i] 

        if char.isspace():
            i += 1
            continue

        if char == DOT_SYMBOL and \
            i + 1 < source_len and \
            source[i + 1] == STRING_QUOTE:
            
            print_string_token = Token(TokenType.SYM, source[i : i + 2])
            tokens.append(print_string_token)
            i += 2
            
            continue

        if char == SIGNATURE_START_SYMBOL:
            i += 1
            found_end_symbol = False

            while i < source_len:
                if source[i] == SIGNATURE_END_SYMBOL:
                    i += 1
                    found_end_symbol = True
                    break
                i += 1

            if not found_end_symbol:
                raise SyntaxError("нет закрывающей скобки для описания сигнатуры функции!")

            continue

        if char == COMMENT_SYMBOL:
            while i < source_len:
                if source[i] == NEWLINE_SYMBOL:
                    break
                i += 1
            i += 1

            continue

        if char == ZERO_SYMBOL and i + 1 < source_len:
            if (source[i + 1] == X_SYMBOL):
                i += 2
                hex_digit_start = i

                if not (source[i].isdigit() or source[i].lower() in HEX_DIGITS):
                    raise SyntaxError("некорректное число в формате hex!")

                while i < source_len and (source[i].isdigit() or source[i].lower() in HEX_DIGITS):
                    i += 1

                hex_str = source[hex_digit_start : i]
                hex_digit_token = Token(TokenType.NUMBER, int(hex_str, 16))
                tokens.append(hex_digit_token)

                continue

        if char.isdigit():
            digit_start = i

            while i < source_len and source[i].isdigit():
                i += 1

            digit_token = Token(TokenType.NUMBER, source[digit_start : i])
            tokens.append(digit_token)

            continue

        if char.isalpha() or char == UNDERSCORE_SYMBOL:
            word_start = i

            while i < source_len and (source[i].isalnum() or source[i] == '_'):
                i += 1

            word_token = Token(TokenType.WORD, source[word_start : i])
            tokens.append(word_token)

            continue

        tokens.append(Token(TokenType.SYM, char))
        i += 1

    return tokens


def preprocess(source_file: str, included_files=None) -> str:
    if included_files is None:
        included_files = set()

    path = os.path.abspath(source_file)

    if path in included_files:
        chain = " -> ".join(included_files) + " -> " + path
        raise RuntimeError(f"повторное включение: {chain}!")
    if not os.path.exists(path):
        raise FileNotFoundError(f"файл {path} не найден!")

    included_files.add(path)
    base_directory = os.path.dirname(path) 
    out = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            sline = line.strip()

            if sline.startswith(REQUIRE_DIRECTIVE):
                if "<" not in sline or ">" not in sline:
                    raise SyntaxError(f"неверный синтаксис {REQUIRE_DIRECTIVE} в {path}:\n{sline}!")

                file_to_include = sline[sline.index("<") + 1 : sline.index(">")].strip()
                include_path = os.path.join(base_directory, file_to_include)
                out.append(preprocess(include_path, included_files))

            else:
                out.append(line)

    return "".join(out)


def main(source_file: str, instr_file: str, data_file: str) -> None:
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""

    source = preprocess(source_file)
    tokens = tokenize(source)
    
    print(source)
    for token in tokens:
        print(token)


if __name__ == "__main__":
    assert (
        len(sys.argv) == 4
    ), "Неверные аргументы: translator.py <input_file> <target_instructions_file> <target_data_file>"
    _, source_file, target_instructions_file, target_data_file = sys.argv
    main(source_file, target_instructions_file, target_data_file)
