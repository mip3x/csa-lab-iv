# csa-lab-iv
4-ая лабораторная работа в рамках дисциплины "Архитектура компьютерных систем"

`Вариант`: `forth | cisc | harv | hw | tick | binary | trap | port | pstr | prob1 | vector`

## Язык программирования

### Синтаксис

Форма Бэкуса-Науэра:

```ebnf
<program> ::= <terms>

<terms> ::= <term>*                     

<term> ::= <number>
            | <string>
            | <ident>
            | <declaration>
            | <definition>
            | <if_stmt>
            | <loop_stmt>
            | <trap_block>
            | <require>

<declaration> ::= "var" <ident>
            | "str" <ident> <string>
            | "port" <ident> <number>
            | "vector" <number> ":" <ident_list>

<definition> ::= ":" <ident> <body> ";"

<if_stmt> ::= "if" <body> ("else" <body>)? "then"

<loop_stmt> ::= "begin" <body> "until"

<trap_block> ::= "trap" <ident> <body> "endtrap"

<require> ::= "require" <string>

<ident_list> ::= <ident> ("," <ident>)*

<number> ::= <decimal> | <hexadecimal>

<decimal> ::= <digit>+                           

<hexadecimal> ::= "0x" <hex_digit>+                  

<ident> ::= <letter> (<letter> | <digit> | "_")*

<string> ::= [^"]

<letter> ::= [a-zA-Z]
<digit> ::= [0-9]
<hex_digit> ::= <digit> | [a-fA-F]
```
