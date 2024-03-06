.CODE 16

@ r0 = sector number + return value, r14 = link register
@ We also need to work with r1~6
PUSH	{r1-r6}
PUSH	{r14}

@ We have two sectors where there would normally be just one
@ Copy original value into r1
MOV		r1, r0

@ Calculate bank number from sector number
LSR		r0, r0, #0x4 @ r1 = r0 @ 0x10

@ Change flash bank (instruction injected by patcher)
.byte	0xF7, 0x00, 0x00, 0x00 @ bl SetFlashBank

@ Double the sector number (r0 = r1 << 1)
LSL		r0, r1, #0x1

erase_sector_1m_start:
	@ Calculate actual sector index from sector number
	MOV		r2, #0x1F
	MOV		r1, r0
	AND		r1, r1, r2
	
	@ Calculate the sector base address
	MOV		r2, #0xE0
	LSL		r2, r2, #0x14
	LSL		r1, r1, #0xB
	ORR		r1, r1, r2
	
	@ Execute sector erase sequence
	MOV		r2, #0xE0
	LSL		r2, r2, #0xC
	MOV		r3, r2
	ADD		r2, #0x55
	LSL		r2, r2, #0x8
	ADD		r2, #0x55
	ADD		r3, #0x2A
	LSL		r3, r3, #0x8
	ADD		r3, #0xAA
	
	MOV		r4, #0xAA
	STRB	r4, [r2] @ 0xE005555 = 0xAA
	MOV		r5, #0x55
	STRB	r5, [r3] @ 0xE002AAA = 0x55
	MOV		r5, #0x80
	STRB	r5, [r2] @ 0xE005555 = 0x80
	STRB	r4, [r2] @ 0xE005555 = 0xAA
	MOV		r5, #0x55
	STRB	r5, [r3] @ 0xE002AAA = 0x55
	MOV		r5, #0x30
	STRB	r5, [r1] @ SA = 0x30
	
	@ Wait for erased sector
		check_sa_1m_start:
		NOP
		LDRB	r5, [r1] @ Check SA
		CMP		r5, #0xFF
		BNE		check_sa_1m_start
	
	@ Check if current sector is even (1/2) or odd (2/2)
	MOV		r1, r0
	MOV		r2, #0x1
	AND		r1, r1, r2
	CMP		r1, #0x0
	BNE		erase_sector_1m_end
	ADD		r0, #0x1
	B		erase_sector_1m_start

erase_sector_1m_end:

@ restore registers
POP		{r0}
MOV		r14, r0
POP		{r1-r6}

@ return value
MOV		r0, #0x0

BX		r14
