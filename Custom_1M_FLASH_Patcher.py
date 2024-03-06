#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Custom 1M FLASH Patcher
# Author: Lesserkuma (github.com/lesserkuma)

import struct, sys, re, os, copy, hashlib

print("Custom 1M FLASH Patcher v2.0\nby Lesserkuma\n")

patch_data = {
	"ProgramFlashSector_Bootleg": bytearray.fromhex("FEB400B5021CF70000001F231A401203E0273F05174310263602E0221203131C5532120255322A331B02AA33AA24147055251D70A02515700D1C0C783C70C0463D78AC42FBD101310137013E002EEDD101BC8646FEBC00207047"),
	"SetFlashBank_Bootleg_1M": bytearray.fromhex("90221205002802D1002010707047012010707047"),
	"EraseFlashSector_Bootleg_1M": bytearray.fromhex("7EB400B5011C0009F700000048001F22011C1140E0221205C9021143E0221203131C5532120255322A331B02AA33AA24147055251D7080251570147055251D7030250D70C0460D78FF2DFBD1011C01221140002901D10130D9E701BC86467EBC00207047"),
	"ReadFlashId_Bootleg_1M": bytearray.fromhex("09200002C23070475061746368206279204C4B00"),
	"EraseFlashSector_Bootleg_512K": bytearray.fromhex("7EB400B5011C000948001F22011C1140E0221205C9021143E0221203131C5532120255322A331B02AA33AA24147055251D7080251570147055251D7030250D70C0460D78FF2DFBD1011C01221140002901D10130D9E701BC86467EBC00207047"),
	"ReadFlashId_Bootleg_512K": bytearray.fromhex("04B490221205002802D10020107002E000201070FFE7D4200002BF3004BC70475061746368206279204C4B00"),
}

def ErrorExit(msg):
	print(msg)
	input("Press ENTER to exit.\n")
	sys.exit(1)

if len(sys.argv) != 2: ErrorExit(f"Error: No file specified. Drag & drop your file onto the executable or run from terminal like so:\n{os.path.split(sys.argv[0])[1]} file.gba\n")

file = sys.argv[1]
print(f"File: {file}")
try:
	with open(file, "rb") as f: buffer = bytearray(f.read())
	if buffer[0xB2] != 0x96: ErrorExit("\nError: Invalid GBA header.")
	rom_hash = hashlib.sha256(buffer).digest()
except Exception as e:
	ErrorExit("\n" + str(e))

print("")
print("Title: " + buffer[0xA0:0xAC].decode("ASCII", "ignore"))
print("Game Code: " + buffer[0xAC:0xB0].decode("ASCII", "ignore"))

flashlibs = []
supported_flashlibs = [ "FLASH1M_V103", "FLASH1M_V102", "FLASH512_V133", "FLASH512_V131", "FLASH512_V130", "FLASH_V126", "FLASH_V125", "FLASH_V124", "FLASH_V123", "FLASH_V121", "FLASH_V120" ]
for temp in supported_flashlibs:
	pos = 0
	while True:
		newpos = buffer[pos:].find(temp.encode("ASCII"))
		if newpos == -1: break
		pos = pos + newpos + len(temp)
		flashlibs.append((temp, pos - len(temp)))

if len(flashlibs) == 0: ErrorExit("\nError: Loaded file doesn’t appear to be using the 1M FLASH or 512K FLASH save type.\n")

for (flashlib, offset) in flashlibs:
	print("")
	print("Backup library:".ljust(20) + flashlib)

	if flashlib in ("FLASH1M_V103", "FLASH1M_V102", "FLASH512_V133", "FLASH512_V131", "FLASH512_V130"):
		offset += 0x10
	else:
		offset += 0xC
	offset = struct.unpack("<I", buffer[offset:offset+4])[0] - 0x8000000
	print("Base offset:".ljust(20) + f"0x{offset:X}")
	
	# SwitchFlashBank
	if "FLASH1M" in flashlib:
		func_size = 0x1C
		o_SetFlashBank = buffer.find(bytearray.fromhex("0006000E054BAA211970054A55211170B0211970E021090508707047"))
		print("SwitchFlashBank:".ljust(20) + f"0x{o_SetFlashBank:X}", end="")
		if o_SetFlashBank == -1:
			print("\n- Stubbed function or already patched.")
			input("Press ENTER to continue.\n")
			continue
		print(f" (0x{func_size:X} bytes)")
		func_bytes_head = bytearray()
		func_bytes_tail = bytearray()
		func_bytes_body = copy.copy(patch_data["SetFlashBank_Bootleg_1M"])
		func_bytes_body += bytearray(func_size - len(func_bytes_body))
		func_bytes = func_bytes_body
		if len(func_bytes) > func_size: ErrorExit("\nError: Not enough space for the new code.")
		buffer[o_SetFlashBank:o_SetFlashBank+len(func_bytes)] = func_bytes

	# EraseFlashSector
	if "FLASH1M" in flashlib:
		if flashlib == "FLASH1M_V103":
			o_EraseFlashSector = offset + 0xC
		elif flashlib == "FLASH1M_V102":
			o_EraseFlashSector = offset + 0x8
		o_EraseFlashSector = struct.unpack("<I", buffer[o_EraseFlashSector:o_EraseFlashSector+4])[0] - 0x8000000 - 1
		print("EraseFlashSector:".ljust(20) + f"0x{o_EraseFlashSector:X}", end="")
		func_bytes_head = bytearray.fromhex("F0B5 90B0")
		func_bytes_tail = bytearray.fromhex("10B0 F0BC 02BC 0847")
		func_bytes_body = copy.copy(patch_data["EraseFlashSector_Bootleg_1M"])
		func_size = buffer[o_EraseFlashSector:].find(func_bytes_tail)
		if buffer[o_EraseFlashSector:o_EraseFlashSector + len(func_bytes_head)] != func_bytes_head or func_size == -1:
			print("\n- Stubbed function or already patched.")
			input("Press ENTER to continue.\n")
			continue
		func_size += len(func_bytes_tail)
		print(f" (0x{func_size:X} bytes)")
		
		flashbank_pointer_offset = func_bytes_body.find(bytearray.fromhex("F7000000"))
		flashbank_pointer = (((o_EraseFlashSector + flashbank_pointer_offset) - o_SetFlashBank) >> 1) + 2
		flashbank_pointer = (0x1000000 - flashbank_pointer) & 0xFFFFFF | (0xF7 << 24)
		func_bytes_body[flashbank_pointer_offset:flashbank_pointer_offset+2] = struct.pack("<H", flashbank_pointer >> 16 & 0xFFFF)
		func_bytes_body[flashbank_pointer_offset+2:flashbank_pointer_offset+4] = struct.pack("<H", flashbank_pointer & 0xFFFF)

		func_bytes_body += bytearray(func_size - len(func_bytes_body))
		func_bytes = func_bytes_body
		if len(func_bytes) > func_size: ErrorExit("\nError: Not enough space for the new code.")
		buffer[o_EraseFlashSector:o_EraseFlashSector+len(func_bytes)] = func_bytes
	else:
		if flashlib == "FLASH512_V133":
			o_EraseFlashSector = offset + 0xC
		else:
			o_EraseFlashSector = offset + 0x8
		o_EraseFlashSector = struct.unpack("<I", buffer[o_EraseFlashSector:o_EraseFlashSector+4])[0] - 0x8000000 - 1
		print("EraseFlashSector:".ljust(20) + f"0x{o_EraseFlashSector:X}", end="")
		if flashlib in ("FLASH_V121", "FLASH_V120"):
			func_bytes_head = bytearray.fromhex("80B5 94B0 6F46 391C 0880 381C 0188 0F29")
			func_bytes_tail = bytearray.fromhex("14B0 80BC 02BC 0847")
		else:
			func_bytes_head = bytearray.fromhex("70B5 4646 40B4 90B0")
			func_bytes_tail = bytearray.fromhex("10B0 08BC 9846 70BC 02BC 0847")
		func_bytes_body = copy.copy(patch_data["EraseFlashSector_Bootleg_512K"])
		func_size = buffer[o_EraseFlashSector:].find(func_bytes_tail)
		if buffer[o_EraseFlashSector:o_EraseFlashSector + len(func_bytes_head)] != func_bytes_head or func_size == -1:
			print("\n- Stubbed function or already patched.")
			input("Press ENTER to continue.\n")
			continue
		func_size += len(func_bytes_tail)
		print(f" (0x{func_size:X} bytes)")
		
		func_bytes_body += bytearray(func_size - len(func_bytes_body))
		func_bytes = func_bytes_body
		if len(func_bytes) > func_size: ErrorExit("\nError: Not enough space for the new code.")
		buffer[o_EraseFlashSector:o_EraseFlashSector+len(func_bytes)] = func_bytes

	# ProgramFlashSector
	if "FLASH1M" in flashlib:
		if flashlib == "FLASH1M_V103":
			o_ProgramFlashSector = offset + 0x4
		elif flashlib == "FLASH1M_V102":
			o_ProgramFlashSector = offset
		o_ProgramFlashSector = struct.unpack("<I", buffer[o_ProgramFlashSector:o_ProgramFlashSector+4])[0] - 0x8000000 - 1
		print("ProgramFlashSector:".ljust(20) + f"0x{o_ProgramFlashSector:X}", end="")
		func_bytes_head = bytearray.fromhex("F0B5 90B0 0F1C")
		func_bytes_tail = bytearray.fromhex("10B0 F0BC 02BC 0847")
		func_bytes_body = copy.copy(patch_data["ProgramFlashSector_Bootleg"])
		func_size = buffer[o_ProgramFlashSector:].find(func_bytes_tail)
		if buffer[o_ProgramFlashSector:o_ProgramFlashSector + len(func_bytes_head)] != func_bytes_head or func_size == -1:
			print("\n- Stubbed function or already patched.")
			input("Press ENTER to continue.\n")
			continue
		func_size += len(func_bytes_tail)
		print(f" (0x{func_size:X} bytes)")

		erase_pointer_offset = func_bytes_body.find(bytearray.fromhex("F7000000"))
		erase_pointer = (((o_ProgramFlashSector + erase_pointer_offset) - o_EraseFlashSector) >> 1) + 2
		erase_pointer = (0x1000000 - erase_pointer) & 0xFFFFFF | (0xF7 << 24)
		func_bytes_body[erase_pointer_offset:erase_pointer_offset+2] = struct.pack("<H", erase_pointer >> 16 & 0xFFFF)
		func_bytes_body[erase_pointer_offset+2:erase_pointer_offset+4] = struct.pack("<H", erase_pointer & 0xFFFF)

		func_bytes_body += bytearray(func_size - len(func_bytes_body))
		func_bytes = func_bytes_body
		if len(func_bytes) > func_size: ErrorExit("\nError: Not enough space for the new code.")
		buffer[o_ProgramFlashSector:o_ProgramFlashSector+len(func_bytes)] = func_bytes
	else:
		if flashlib in ("FLASH512_V133"):
			o_ProgramFlashSector = offset + 0x4
		else:
			o_ProgramFlashSector = offset
		o_ProgramFlashSector = struct.unpack("<I", buffer[o_ProgramFlashSector:o_ProgramFlashSector+4])[0] - 0x8000000 - 1
		print("ProgramFlashSector:".ljust(20) + f"0x{o_ProgramFlashSector:X}", end="")
		if flashlib in ("FLASH_V121", "FLASH_V120"):
			func_bytes_head = bytearray.fromhex("90B5 A0B0")
			func_bytes_tail = bytearray.fromhex("20B0 90BC 02BC 0847")
		else:
			func_bytes_head = bytearray.fromhex("F0B5 4F46 4646 C0B4 98B0")
			func_bytes_tail = bytearray.fromhex("18B0 18BC 9846 A146 F0BC 02BC 0847")
		func_bytes_body = copy.copy(patch_data["ProgramFlashSector_Bootleg"])
		func_size = buffer[o_ProgramFlashSector:].find(func_bytes_tail)
		if buffer[o_ProgramFlashSector:o_ProgramFlashSector + len(func_bytes_head)] != func_bytes_head or func_size == -1:
			print("\n- Stubbed function or already patched.")
			input("Press ENTER to continue.\n")
			continue
		func_size += len(func_bytes_tail)
		print(f" (0x{func_size:X} bytes)")

		erase_pointer_offset = func_bytes_body.find(bytearray.fromhex("F7000000"))
		erase_pointer = (((o_ProgramFlashSector + erase_pointer_offset) - o_EraseFlashSector) >> 1) + 2
		erase_pointer = (0x1000000 - erase_pointer) & 0xFFFFFF | (0xF7 << 24)
		func_bytes_body[erase_pointer_offset:erase_pointer_offset+2] = struct.pack("<H", erase_pointer >> 16 & 0xFFFF)
		func_bytes_body[erase_pointer_offset+2:erase_pointer_offset+4] = struct.pack("<H", erase_pointer & 0xFFFF)

		func_bytes_body += bytearray(func_size - len(func_bytes_body))
		func_bytes = func_bytes_body
		if len(func_bytes) > func_size: ErrorExit("\nError: Not enough space for the new code.")
		buffer[o_ProgramFlashSector:o_ProgramFlashSector+len(func_bytes)] = func_bytes

	# ReadFlashId
	if flashlib in ("FLASH_V121", "FLASH_V120"):
		o_ReadFlashId = buffer.find(bytearray.fromhex("90B593B06F46391D081C"))
		func_bytes_head = bytearray.fromhex("90B5 93B0")
		func_bytes_tail = bytearray.fromhex("13B0 90BC 02BC 0847")
	else:
		o_ReadFlashId = buffer.find(bytearray.fromhex("034A101C08E000005555000EAA2A000E")) - 0x20
		func_bytes_head = bytearray.fromhex("30B5 91B0")
		func_bytes_tail = bytearray.fromhex("11B0 30BC 02BC 0847")
	print("ReadFlashId:".ljust(20) + f"0x{o_ReadFlashId:X}", end="")
	func_size = buffer[o_ReadFlashId:].find(func_bytes_tail)
	if buffer[o_ReadFlashId:o_ReadFlashId + len(func_bytes_head)] != func_bytes_head or func_size == -1:
		print("\n- Stubbed function or already patched.")
		input("Press ENTER to continue.\n")
		continue
	func_size += len(func_bytes_tail)
	print(f" (0x{func_size:X} bytes)")
	if "FLASH1M" in flashlib:
		func_bytes_body = copy.copy(patch_data["ReadFlashId_Bootleg_1M"])
	else:
		func_bytes_body = copy.copy(patch_data["ReadFlashId_Bootleg_512K"])
	func_bytes_body += bytearray(func_size - len(func_bytes_body))
	func_bytes = func_bytes_body
	if len(func_bytes) > func_size: ErrorExit("\nError: Not enough space for the new code.")
	buffer[o_ReadFlashId:o_ReadFlashId+len(func_bytes)] = func_bytes	

if hashlib.sha256(buffer).digest() == rom_hash:
	print("\nThis file could not be patched.\n")
else:
	outfile = os.path.splitext(file)[0] + "_patched.gba"
	with open(outfile, "wb") as f: f.write(buffer)
	print(f"\nPatched file written to: {outfile}\n")

input("Press ENTER to exit.\n")
