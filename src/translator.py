#!/usr/bin/python3

import sys
from typing import List, Dict, Any, Tuple

from ast_nodes import Program
from tokenizer import Token, tokenize
from preprocessor import preprocess
from parser import Parser
from isa import to_bytes as isa_to_bytes, to_hex as isa_to_hex, Opcode
from codegen import compile_program


def words_to_bytes_be(words: List[int]) -> bytes:
    out = bytearray()
    for word in words:
        word &= 0xFFFFFFFF
        out.extend(
            (
                (word >> 24) & 0xFF,
                (word >> 16) & 0xFF,
                (word >> 8) & 0xFF,
                word & 0xFF
             )
        )

    return bytes(out)


def translate(source_file : str) -> Tuple[List[Dict[str, Any]], List[int]]:
    source : str = preprocess(source_file)
    tokens : List[Token] = tokenize(source)
    
    print(source)
    print()

    for token in tokens:
        print(token)
    print()

    parser = Parser(tokens)
    ast : Program = parser.parse()
    print(ast)
    print()

    instructions, data_words = compile_program(ast)
    if not instructions:
        instructions = [
            {"opcode": Opcode.HALT}
        ]

    return instructions, data_words


def main(source_file: str, instr_file: str, data_file: str) -> None:
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""

    instructions, data_words = translate(source_file)
    instruction_memory_bytes = isa_to_bytes(instructions)
    data_memory_bytes = words_to_bytes_be(data_words)

    with open(instr_file, "wb") as file:
        file.write(instruction_memory_bytes)

    with open(data_file, "wb") as file:
        file.write(data_memory_bytes)

    listing_file = instr_file + ".hex"
    hex_listing = isa_to_hex(instructions)
    with open(listing_file, "w", encoding="utf-8") as file:
        file.write(hex_listing)
    
    print(data_words)
    print(hex_listing)


if __name__ == "__main__":
    assert (
        len(sys.argv) == 4
    ), "Неверные аргументы: translator.py <input_file> <target_instructions_file> <target_data_file>"
    _, source_file, target_instructions_file, target_data_file = sys.argv
    main(source_file, target_instructions_file, target_data_file)
