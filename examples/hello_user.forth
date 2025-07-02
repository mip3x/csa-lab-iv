\ D - Data Stack ; R - Return Stack
: print-string ( str -- )
    dup             \ D: [addrof(str):addrof(str)]
    @               \ D: [addrof(str):len(str)]

    times           \ D: [addrof(str)]                      R: [len(str)]
        1 +         \ D: [addrof(str)+1]                    R: [len(str)]
        dup         \ D: [addrof(str)+1:addrof(str)+1]      R: [len(str)]
        @           \ D: [addrof(str)+1:*addrof(str)+1]     R: [len(str)]
        emit        \ D: [addrof(str)+1]                    R: [len(str)] -- *addrof(str)+1 -> STDOUT
    next            \ D: [addrof(str)+1]                    R: [len(str)-1]
;

: read-symbol ( -- )
    _disable-int_

    un-buffer-ptr 1 +
    un-buffer-ptr !

    un-actual-size un-buffer-size =

    if 
        1 overflow-error !
        error-msg print-string
        cr
        _iret_
    then

    key dup CR-char = if iret then dup NL-char = if iret then
    un-buffer-ptr !

    un-actual-size 1 +
    un-actual-size !

    _enable-int_
;

: read-string ( -- )
    0 un-actual-size !
    _enable-int_
    _disable-int_

    overlflow-error 1 = if _exit_ then

    un-actual-size username-buffer !
;


vector 1 : read-symbol

str question-msg "What is your name?"
str error-msg "Buffer overflow!"

256 const un-buffer-size
un-buffer-size alloc username-buffer
var un-buffer-ptr
var un-actual-size
var overflow-error

str hello-msg "Hello, "
33 const exclamation-mark
13 const CR-char
10 const NL-char


question-msg print-string
cr

0 overflow-error !
username-buffer un-buffer-ptr !

read-string
hello-msg print-string
username-buffer print-string
