section .data
    null_term: word 0

section .text
    read_char:
        in
        cmp null_term
        je .exit
        out
        jmp .read_char
    exit:
        hlt
