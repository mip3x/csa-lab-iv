from enum import Enum

from ast_nodes import *


class Parser:
    def __init__(self, tokens: str):
        self.tokens = tokens
        pass

    def parse(self) -> Program:
        print("Parsing started...")
        return None


class ParserError(Exception):
    pass


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