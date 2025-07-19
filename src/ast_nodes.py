from typing import List


class Node:
    pass


class UnitItem(Node):
    pass


class Statement(UnitItem):
    pass


class Binding(UnitItem):
    pass


class LoopStatement(Statement):
    pass


class Declaration(Binding):
    pass


class Ident(Statement):
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"Ident(value={self.value})"


class String(Statement):
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"String(value={self.value})"


class Number(Statement):
    def __init__(self, value: int):
        self.value = value

    def __repr__(self):
        return f"Number(value={self.value})"


class Body(Node):
    def __init__(self, statements: List[Statement]):
        self.statements = statements

    def __repr__(self):
        return f"Body(statements={self.statements})"


class Program(Node):
    def __init__(self, bindings: List[Binding], body: Body):
        self.bindings = bindings
        self.body = body

    def __repr__(self):
        return f"Program(bindings={self.bindings}, body={self.body})"


class Definition(Binding):
    def __init__(self, ident: Ident, body: Body):
        self.ident = ident
        self.body = body

    def __repr__(self):
        return f"Definition(ident={self.ident}, body={self.body})"


class Vector(Binding):
    def __init__(self, number: Number, ident: Ident):
        self.number = number
        self.ident = ident

    def __repr__(self):
        return f"Vector(number={self.number}, ident={self.ident})"


class Variable(Declaration):
    def __init__(self, ident: Ident, number: Number):
        self.ident = ident
        self.number = number

    def __repr__(self):
        return f"Variable(ident={self.ident}, number={self.number})"


class StringLiteral(Declaration):
    def __init__(self, ident: Ident, string: String):
        self.ident = ident
        self.string = string

    def __repr__(self):
        return f"StringLiteral(ident={self.ident}, string={self.string})"


class Const(Declaration):
    def __init__(self, number: Number, ident: Ident):
        self.number = number
        self.ident = ident

    def __repr__(self):
        return f"Const(number={self.number}, ident={self.ident})"


class IfStatement(Statement):
    def __init__(self, ifbody: Body, elsebody: Body = None):
        self.ifbody = ifbody
        self.elsebody = elsebody

    def __repr__(self):
        return f"IfStatement(ifbody={self.ifbody}, elsebody={self.elsebody})"


class BeginLoop(LoopStatement):
    def __init__(self, body: Body):
        self.body = body

    def __repr__(self):
        return f"BeginLoop(body={self.body})"


class TimesLoop(LoopStatement):
    def __init__(self, body: Body):
        self.body = body

    def __repr__(self):
        return f"TimesLoop(body={self.body})"