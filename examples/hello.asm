section .data
    curr_char: word 1
    hellow: db "hello world"
    null_term: word 0

section .text
    print:
        ld $curr_char  ; загружаю символ по адресу curr_char
        cmp #0  ; сравниваю, закончилась ли строка
        je .exit
        out
        ld curr_char
        add #1
        st curr_char
        jmp .print
    exit:
        hlt
