.CODE 16

@ r0 = sector number + return value, r1 = pointer to data, r14 = link register
@ We also need to work with r1~7
PUSH	{r1-r7}
PUSH	{r14}

@ Erase sector (instruction injected by patcher)
MOV		r2, r0
.byte	0xF7, 0x00, 0x00, 0x00 @ bl EraseFlashSector

@ Calculate actual sector index from sector number
MOV		r3, #0x1F
AND		r2, r2, r3
LSL		r2, r2, #0xC

@ Flash memory target address pointer
MOV		r7, #0xE0
LSL		r7, r7, #0x14
ORR		r7, r7, r2

@ Initialize counter
MOV		r6, #0x10
LSL		r6, r6, #0x8

@ Execute write sequence
MOV		r2, #0xE0
LSL		r2, r2, #0xC
MOV		r3, r2
ADD		r2, #0x55
LSL		r2, r2, #0x8
ADD		r2, #0x55
ADD		r3, #0x2A
LSL		r3, r3, #0x8
ADD		r3, #0xAA

@ Loop
	write_loop_start:
	MOV		r4, #0xAA
	STRB	r4, [r2] @ 0xE005555 = 0xAA
	MOV		r5, #0x55
	STRB	r5, [r3] @ 0xE002AAA = 0x55
	MOV		r5, #0xA0
	STRB	r5, [r2] @ 0xE005555 = 0xA0
	MOV		r5, r1
	LDRB	r4, [r1] @ Load next value into r4 (PD)
	STRB	r4, [r7] @ PA = PD
	
	@ Wait for written data
		check_data_start:
		NOP
		LDRB	r5, [r7] @ read back
		CMP		r4, r5
		BNE		check_data_start

	ADD		r1, r1, #0x1
	ADD		r7, r7, #0x1
	SUB		r6, #0x1
	CMP		r6, #0x0
	BNE		write_loop_start

@ restore registers
POP		{r0}
MOV		r14, r0
POP		{r1-r7}

@ return value
MOV		r0, #0x0

BX		r14
