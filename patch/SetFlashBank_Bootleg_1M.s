.CODE 16

@ r0 = bank index, r14 = link register

MOV		r2, #0x90
LSL		r2, r2, #0x14
CMP		r0, #0x0
BNE		bank1_1m
bank0_1m:
MOV		r0, #0x0
STRB	r0, [r2]
BX		r14
bank1_1m:
MOV		r0, #0x1
STRB	r0, [r2]
BX		r14
