\ D - Data Stack ; R - Return Stack
: print_string ( str -- )
    dup             \ D: [addrof(str):addrof(str)]
    @               \ D: [addrof(str):len(str)]

    times           \ D: [addrof(str)]                      R: [len(str)]
        1 +         \ D: [addrof(str)+1]                    R: [len(str)]
        dup         \ D: [addrof(str)+1:addrof(str)+1]      R: [len(str)]
        @           \ D: [addrof(str)+1:*addrof(str)+1]     R: [len(str)]
        emit        \ D: [addrof(str)+1]                    R: [len(str)] -- *addrof(str)+1 -> STDOUT
    next            \ D: [addrof(str)+1]                    R: [len(str)-1]
;

: read_symbol ( -- )
    _disable_int_

    un_buffer_ptr @ 1 +
    un_buffer_ptr !

    un_actual_size @ un_buffer_size =

    if 
        1 overflow_error !
        error_msg print_string
        cr
        _iret_
    then

    key dup CR_char = if _iret_ then dup NL_char = if _iret_ then
    un_buffer_ptr @ !

    un_actual_size @ 1 +
    un_actual_size !

    _enable_int_

    _iret_
;

: read_string ( -- )
    0 un_actual_size !
    _enable_int_
    _disable_int_

    overflow_error 1 = if _exit_ then

    un_actual_size username_buffer !
;


vector 1 : read_symbol

str question_msg "What is your name?"
str error_msg "Buffer overflow!"

const un_buffer_size 256
alloc username_buffer un_buffer_size 
var un_buffer_ptr
var un_actual_size
var overflow_error

str hello_msg "Hello, "
const exclamation_mark 33
const CR_char 13
const NL_char 10


question_msg print_string
cr

0 overflow_error !
username_buffer un_buffer_ptr !

read_string
hello_msg print_string
username_buffer print_string
exclamation_mark emit
