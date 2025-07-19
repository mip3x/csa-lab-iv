import os
from definitions import REQUIRE_DIRECTIVE


class PreprocessError(Exception):
    pass


def preprocess(source_file: str, included_files=None) -> str:
    if included_files is None:
        included_files = set()

    path = os.path.abspath(source_file)

    if path in included_files:
        chain = " -> ".join(included_files) + " -> " + path
        raise PreprocessError(f"повторное включение: {chain}!")
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