; https://gist.github.com/ded-Egor/7e542b838134781f8aa27f3ab1982204

section .data
    result: word 20 ; must be equal `sum`
    sum: word 20
    curr: word 19  ; must be equal `sum - 1`

section .text
    loop:
        ld result
        mod curr
        cmp #0
        je next
        ld result
        add sum
        st result
        jmp loop
    next:
        ld result
        st sum

        ld curr
        add #-1
        st curr
        cmp #1
        je finish
        jmp loop
    finish:
        hlt
