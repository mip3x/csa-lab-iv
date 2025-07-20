from enum import Enum

from ast_nodes import *
from definitions import *
from tokenizer import Token, TokenType


class Keyword(str, Enum):
    IF = "if"
    ELSE = "else"
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

    @classmethod
    def is_keyword(cls, value: str) -> bool:
        try:
            cls(value)
            return True
        except ValueError:
            return False


class Parser:
    def __init__(self, tokens: str):
        self.tokens = tokens
        self.tokens_len = len(tokens)
        self.i = 0

    def __eof(self) -> bool:
        return self.i >= self.tokens_len

    def __go_to_next_token(self) -> None:
        self.i += 1

    def __get_current_token(self) -> Token:
        if self.__eof():
            return None
        return self.tokens[self.i]

    def __parse_string(self) -> String:
        token = self.__get_current_token()
        if not token or token.kind != TokenType.STRING:
            raise ParseError(f"ожидаемый тип ввода - строковый литерал, но считан EOF!")
        
        string = String(value=token.value)
        self.__go_to_next_token()

        return string

    def __parse_ident(self) -> Ident:
        token = self.__get_current_token()
        if not token:
            raise ParseError(f"ожидаемый тип ввода - `ident`, но считан EOF!")

        if Keyword.is_keyword(token.value):
            raise ParseError(f"имя определения {token.value} является ключевым словом! Выберите другое!")

        ident = Ident(value=token.value)
        self.__go_to_next_token()
        
        return ident

    def __parse_body(self, stop_syms: set) -> Body:
        statements : List[Statement] = list()

        while True:
            token = self.__get_current_token()

            if not token:
                if stop_syms:
                    raise ParseError(f"ожидаемый токен - один из множества {str(stop_syms)}, но считан EOF!")
                break
            if token.value in stop_syms:
                break

            statements.append(self.__parse_statement())

        return Body(statements=statements)

    def __parse_if(self) -> IfStatement:
        self.__go_to_next_token() # skip `if` keyword

        ifbody = self.__parse_body(stop_syms={Keyword.ELSE.value, Keyword.THEN.value})
        token = self.__get_current_token()

        if token.value == Keyword.ELSE.value:
            self.__go_to_next_token() # skip `else` keyword

            elsebody = self.__parse_body(stop_syms={Keyword.THEN.value})
            token = self.__get_current_token()
            if not (token and token.value == Keyword.THEN.value):
                raise ParseError(f"ожидался `then`-блок после `else`-блока!")
            
            self.__go_to_next_token() # skip `then` keyword
            return IfStatement(ifbody=ifbody, elsebody=elsebody)

        if not (token and token.value == Keyword.THEN.value):
            raise ParseError(f"ожидался `then`-блок после `if`!")

        self.__go_to_next_token()
        return IfStatement(ifbody=ifbody, elsebody=None)

    def __parse_begin(self) -> BeginLoop:
        self.__go_to_next_token() # skip `begin` keyword

        body = self.__parse_body(stop_syms={Keyword.UNTIL.value})
        token = self.__get_current_token()
        if not (token and token.value == Keyword.UNTIL.value):
            raise ParseError(f"ожидался `until` после `begin`-блока!")
        
        self.__go_to_next_token()
        return BeginLoop(body=body)

    def __parse_times(self) -> TimesLoop:
        self.__go_to_next_token() # skip `times` keyword

        body = self.__parse_body(stop_syms={Keyword.NEXT.value})
        token = self.__get_current_token()
        if not (token and token.value == Keyword.NEXT.value):
            raise ParseError(f"ожидался `next` после `times`-блока!")

        self.__go_to_next_token()
        return TimesLoop(body=body)

    def __parse_number(self) -> Number:
        token = self.__get_current_token()
        if not token:
            raise ParseError(f"ожидаемый тип ввода - `number`, но считан EOF!")

        if token.kind != TokenType.NUMBER:
            self.__go_to_next_token()
            raise ParseError(f"ожидаем тип токена - {str(TokenType.NUMBER)}, но считанный - {str(token.kind)}!")

        num = Number(value=int(token.value))
        self.__go_to_next_token()

        return num

    def __parse_number_or_const(self) -> Number | Const:
        token = self.__get_current_token()
        if not token:
            raise ParseError(f"ожидаемый тип ввода - `number|const`, но считан EOF!")

        if token.kind == TokenType.NUMBER:
            return self.__parse_number()

        if token.kind in (TokenType.WORD, TokenType.SYM):
            ident = self.__parse_ident()
            return Const(ident=ident, number=None)

    def __parse_statement(self) -> Statement:
        token = self.__get_current_token()
        if not token:
            raise ParseError(f"ожидаемый тип ввода - токен, но считан EOF!")

        if token.kind == TokenType.WORD:
            if token.value == Keyword.IF.value:
                return self.__parse_if()
            if token.value == Keyword.BEGIN.value:
                return self.__parse_begin()
            if token.value == Keyword.TIMES.value:
                return self.__parse_times()

        if token.kind == TokenType.NUMBER:
            return self.__parse_number()

        return self.__parse_ident()

    def __parse_definition(self) -> Definition:
        self.__go_to_next_token() # skip `:`

        ident : Ident = self.__parse_ident()
        body : Body = self.__parse_body(stop_syms={DEFINITION_END_SYM})

        token = self.__get_current_token()
        if not (token and token.value == DEFINITION_END_SYM):
            raise ParseError(f"ожидался символ `;` после тела определения!")
        
        self.__go_to_next_token()
        return Definition(ident=ident, body=body)
    
    def __parse_declaration(self) -> Declaration:
        keyword = self.__get_current_token()
        self.__go_to_next_token()

        if keyword.value == Keyword.VAR.value:
            ident = self.__parse_ident()
            return Variable(ident=ident, number=None)
        
        if keyword.value == Keyword.STR.value:
            ident = self.__parse_ident()
            string = self.__parse_string()

            self.__go_to_next_token() # skip string

            return StringLiteral(ident=ident, string=string)

        if keyword.value == Keyword.CONST.value:
            ident = self.__parse_ident()
            number = self.__parse_number() # cancel use another `const` value in `const` declaration
            return Const(ident=ident, number=number)

        if keyword.value == Keyword.ALLOC.value:
            ident = self.__parse_ident()
            number = self.__parse_number_or_const()
            return Alloc(ident=ident, number=number)

        if keyword.value == Keyword.VECTOR.value:
            port = self.__parse_number_or_const()
            token = self.__get_current_token()

            if not (token and token.kind == TokenType.SYM and token.value == DEFINITION_START_SYM):
                raise ParseError("Ожидался `:` в <vector> <num|const> : <handler>!")

            self.__go_to_next_token()
            handler = self.__parse_ident()

            return Vector(port=port, ident=handler)

        raise ParseError(f"неизвестная декларация :(")

    def parse(self) -> Program:
        print("Parsing started...")

        bindings : List[Binding] = list()
        body : List[Statement] = list()

        while not self.__eof():
            token = self.__get_current_token()
            if not token:
                break

            if token.kind == TokenType.SYM and token.value == DEFINITION_START_SYM:
                bindings.append(self.__parse_definition())
                # print(bindings)
                # exit()
                continue

            if token.kind == TokenType.WORD and token.value in \
                (Keyword.VAR.value, Keyword.STR.value, Keyword.CONST.value, \
                 Keyword.ALLOC.value, Keyword.VECTOR.value):
                bindings.append(self.__parse_declaration())
                continue

            body.append(self.__parse_statement())

        return Program(bindings, Body(body))


class ParseError(Exception):
    pass