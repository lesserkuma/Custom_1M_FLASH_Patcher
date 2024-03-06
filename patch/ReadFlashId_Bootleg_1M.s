.CODE 16

@ r0 = return value, r14 = link register

@ 0xC209 = Macronix MX29L010
MOV		r0, #0x09
LSL		r0, r0, #0x8
ADD		r0, #0xC2

BX		r14

.asciz	"Patch by LK"
