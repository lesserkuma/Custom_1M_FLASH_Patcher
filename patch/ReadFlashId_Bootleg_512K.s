.CODE 16

@ r0 = return value, r14 = link register
@ We also need to work with r2
PUSH	{r2}

@ Force flash bank to 0 for 512K
MOV		r2, #0x90
LSL		r2, r2, #0x14
CMP		r0, #0x0
BNE		bank1_512k
bank0_512k:
MOV		r0, #0x0
STRB	r0, [r2]
B		bank_512k_end
bank1_512k:
MOV		r0, #0x0
STRB	r0, [r2]
B		bank_512k_end

bank_512k_end:

@ 0xBFD4 = SST 39VF512
MOV		r0, #0xD4
LSL		r0, r0, #0x8
ADD		r0, #0xBF

POP		{r2}
BX		r14

.asciz	"Patch by LK"
