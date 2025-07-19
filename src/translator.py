#!/usr/bin/python3

import sys
from typing import List

from ast_nodes import Program
from tokenizer import Token, tokenize
from preprocessor import preprocess
from parser import Parser


def main(source_file: str, instr_file: str, data_file: str) -> None:
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""

    source : str = preprocess(source_file)
    tokens : List[Token] = tokenize(source)
    
    print(source)
    for token in tokens:
        print(token)

    parser = Parser(tokens)
    ast : Program = parser.parse()


if __name__ == "__main__":
    assert (
        len(sys.argv) == 4
    ), "Неверные аргументы: translator.py <input_file> <target_instructions_file> <target_data_file>"
    _, source_file, target_instructions_file, target_data_file = sys.argv
    main(source_file, target_instructions_file, target_data_file)
