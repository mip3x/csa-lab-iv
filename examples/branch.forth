: fizz? 3 mod 0 = if ." Fizz" then ;
: buzz? 5 mod 0 = if ." Buzz" then ;
: fizz-buzz? dup fizz? swap buzz? or not ;
    
\ D - Data Stack ; R - Return Stack
: do-fizz-buzz ( n -- )
    1               \ D: [n:1]
    swap            \ D: [1:n]
    times           \ D: [1]        R: [n]
        dup         \ D: [1:1]      R: [n]
        fizz-buzz?  \ D: [1:0/-1]   R: [n]
        if 
            dup .   \ D: [1]        R: [n]
        then
        1 +         \ D: [2]        R: [n]
    next            \ D: [2]        R: [n-1]
;

25 do-fizz-buzz
