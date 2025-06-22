\ D - Data Stack ; R - Return Stack
: sum_1_to_n_times ( n -- sum )
    0               \ D: [n:sum]
    swap            \ D: [sum:n]
    times           \ D: [sum]      R: [n]
        r@          \ D: [sum:n]    R: [n]
        +           \ D: [sum+n]    R: [n]
    next
;

4 sum_1_to_n_times .

\ --- Пример для 4 --- (sum_1_to_n_times)
\ 1) D: [4:0]
\    D: [0:4] 
\    D: [0]         R: [4]
\    D: [0:4]       R: [4]
\    D: [4]         R: [4]
\    D: [4]         R: [3]
\ -------------------- 
\ 2) D: [4:3]       R: [3]
\    D: [4+3=7]     R: [3]
\    D: [7]         R: [2]
\ -------------------- 
\ 3) D: [7:2]       R: [2]
\    D: [7+2=9]     R: [2]
\    D: [9]         R: [1]
\ -------------------- 
\ 4) D: [9:1]       R: [1]
\    D: [9+1=10]    R: [1]
\    D: [10]        R: [0] -> R: [] (drop если 0)
\ -------------------- 
\    D: [10]->OUT   R: []




: sum_1_to_n_begin ( n -- sum )
    0               \ D: [n:sum]
    swap            \ D: [sum:n]
    >r              \ D: [sum]          R: [n]
    begin
       r@           \ D: [sum:n]        R: [n]
       +            \ D: [sum+n]        R: [n]
       r>           \ D: [sum+n:n]      R: []
       1 -          \ D: [sum+n:n-1]    R: []
       >r           \ D: [sum+n]        R: [n-1]
       r@           \ D: [sum+n:n-1]    R: [n-1]  
       0            \ D: [sum+n:n-1:0]  R: [n-1]
       =            \ D: [sum+n:n-1==0] R: [n-1]        n-1==0 будет давать либо 0 (false), либо -1 (true)
    until
       r> drop      \ D: [sum+n]        R: []
;

5 sum_1_to_n_begin . 
