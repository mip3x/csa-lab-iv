# csa-lab-iv

4-ая лабораторная работа в рамках дисциплины "Архитектура компьютерных систем"

`Вариант`: `forth | cisc | harv | hw | tick | binary | trap | port | pstr | prob1 | vector`

## Оглавление

- [Язык программирования](#Язык-программирования)
    - [Синтаксис](#Синтаксис)
    - [Описание конструкций языка](#Описание-конструкций-языка)

## Язык программирования

### Синтаксис

Форма Бэкуса-Науэра:

```ebnf
<program> ::= <bindings> <body>

<bindings> ::= <binding>*

<binding> ::= <definition> | <declaration>

<definition> ::= ":" <ident> <body> ";"

<body> ::= <statement>*

<statement> ::= <number>
            | <string>
            | <ident>
            | <if_stmt>
            | <loop_stmt>
            | <trap_block>
            | <require>

<declaration> ::= "var" <ident> (<number>)?
            | "str" <ident> <string>
            | <number> "const" <ident>
            | <number> "alloc" <ident>
            | "vector" <number> ":" <ident>

<if_stmt> ::= "if" <body> ("else" <body>)? "then"

<loop_stmt> ::= "begin" <body> "until"
            | <number> "times" <body> "next"

<trap_block> ::= "trap" <ident> <body> "endtrap"

<require> ::= "#require" <string>

<number> ::= <decimal> | <hexadecimal>

<decimal> ::= <digit>+                           

<hexadecimal> ::= "0x" <hex_digit>+                  

<ident> ::= <letter> (<letter> | <digit> | "_")*

<string> ::= [^"]

<letter> ::= [a-zA-Z]
<digit> ::= [0-9]
<hex_digit> ::= <digit> | [a-fA-F]
```

### Описание конструкций языка

Подробное описание находится в [этом файле](./docs/prog-lang.md) документации.
