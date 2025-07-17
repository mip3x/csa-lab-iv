#!/usr/bin/python3

import os
import sys

from definitions import *

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


def main(source_file: str, instr_file: str, data_file: str):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""

    source = preprocess(source_file)
    print(source)


if __name__ == "__main__":
    assert (
        len(sys.argv) == 4
    ), "Неверные аргументы: translator.py <input_file> <target_instructions_file> <target_data_file>"
    _, source_file, target_instructions_file, target_data_file = sys.argv
    main(source_file, target_instructions_file, target_data_file)
