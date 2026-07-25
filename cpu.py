ram = bytearray(65536)  # 64KB of RAM

registers = bytearray(7)  # 7 registers: A, B, C, D, E, H, L
# pairs: b/c, d/e, h/l

flags = 0x00 # a single byte (plain int, masked & 0xFF), with bit-level check/set/clear operations at specific positions 
# (Sign=7, Zero=6, AC=4, Parity=2, Carry=0)

pc = 0x0000  # Program Counter (16-bit); masked & 0xFFFF
# starts at 0x0000, but can be set to any address in the 64KB address space

sp = 0x0000  # Stack Pointer (16-bit); masked & 0xFFFF
# starts at 0x0000 as a placeholder; real programs initialize SP themselves via LXI SP before using the stack

CODE_TO_INDEX = {0b000: 1, 0b001: 2, 0b010: 3, 0b011: 4, 0b100: 5, 0b101: 6, 0b111: 0}
# This dictionary maps 3-bit register codes to their corresponding indices in the registers array.

RP_CODE_TO_INDEX = {0b00: (1, 2), 0b01: (3, 4), 0b10: (5, 6)}
# This dictionary maps 2-bit register pair codes to their corresponding indices in the registers array.

def fetch_byte():
    """
    Fetches a single byte from RAM at the current program counter (PC) address, increments the PC, and returns the byte.
    """
    global pc
    byte = ram[pc]
    pc = (pc + 1) & 0xFFFF  # Increment PC and wrap around at 16 bits
    return byte


# <-- MOV Instruction Family -->
# A MOV instruction has the bit pattern 01DDDSSS, where DDD is the destination register code and SSS is the source register code.

def mov_reg_to_reg(opcode):
    """
    Moves the value from one register to another.
    """
    ddd = (opcode >> 3) & 0b111  # Destination register code
    sss = opcode & 0b111         # Source register code

    # Fetch the value from the source register
    source_value = registers[CODE_TO_INDEX[sss]]

    # Store the value in the destination register
    registers[CODE_TO_INDEX[ddd]] = source_value


def get_hl_address():
    """
    Returns the 16-bit address formed by the H and L registers.
    H is the high byte and L is the low byte.
    """
    h = registers[5]  # H register
    l = registers[6]  # L register
    return (h << 8) | l  # Combine H and L to form a 16-bit address

def mem_to_reg(opcode):
    """
    Moves the value from memory at the address pointed to by the HL register pair into a destination register.
    """

    ddd = (opcode >> 3) & 0b111  # Destination register code
    hl_address = get_hl_address()  # Get the address from H and L registers

    # Fetch the value from memory at the address pointed to by HL
    value = ram[hl_address]

    # Store the value in the destination register
    registers[CODE_TO_INDEX[ddd]] = value

def reg_to_mem(opcode):
    """
    Moves the value from a source register into memory at the address pointed to by the HL register pair.
    """
    sss = opcode & 0b111  # Source register code
    hl_address = get_hl_address()  # Get the address from H and L registers

    # Fetch the value from the source register
    value = registers[CODE_TO_INDEX[sss]]

    # Store the value in memory at the address pointed to by HL
    ram[hl_address] = value


# <-- Flag Operations -->

def set_or_clear_flag(flags, mask, condition):
    """
    Sets or clears a specific flag in the flags byte based on the condition.
    :param flags: The current flags byte.
    :param mask: The bitmask for the specific flag to set or clear.
    :param condition: If True, set the flag; if False, clear the flag.
    :return: The updated flags byte.
    """
    if condition:
        return (flags | mask) & 0xFF  # Set the flag
    else:
        return (flags & ~mask) & 0xFF  # Clear the flag

def update_zsp_flags(flags, value):
    """
    Updates the Zero, Sign, and Parity flags based on the given value.
    :param value: The value to check for flag updates.
    :param flags: The current flags byte.
    :return: The updated flags byte.
    """
    # Update Zero flag (bit 6)
    flags = set_or_clear_flag(flags, 0b01000000, value == 0)

    # Update Sign flag (bit 7)
    flags = set_or_clear_flag(flags, 0b10000000, (value & 0x80) != 0)

    # Update Parity flag (bit 2)
    parity = value.bit_count() % 2 == 0
    flags = set_or_clear_flag(flags, 0b00000100, parity)
    return flags

def inr(opcode):
    """
    Increments the value of a register or memory location by 1.
    Updates the Zero, Sign, and Parity flags based on the result.
    """
    global flags
    ddd = (opcode >> 3) & 0b111  # Destination register code

    if ddd == 0b110:  # If destination is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
        value = (value + 1) & 0xFF  # Increment and wrap around at 8 bits
        ram[hl_address] = value
    else:
        value = registers[CODE_TO_INDEX[ddd]]
        value = (value + 1) & 0xFF  # Increment and wrap around at 8 bits
        registers[CODE_TO_INDEX[ddd]] = value

    # Update flags based on the new value
    flags = update_zsp_flags(flags, value)

def dcr(opcode):
    """
    Decrements the value of a register or memory location by 1.
    Updates the Zero, Sign, and Parity flags based on the result.
    """
    global flags
    ddd = (opcode >> 3) & 0b111  # Destination register code

    if ddd == 0b110:  # If destination is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
        value = (value - 1) & 0xFF  # Decrement and wrap around at 8 bits
        ram[hl_address] = value
    else:
        value = registers[CODE_TO_INDEX[ddd]]
        value = (value - 1) & 0xFF  # Decrement and wrap around at 8 bits
        registers[CODE_TO_INDEX[ddd]] = value

    # Update flags based on the new value
    flags = update_zsp_flags(flags, value)

def mvi(opcode):
    """
    Moves an immediate value into a register or memory location.
    The immediate value is fetched from the next byte in RAM.
    """
    
    ddd = (opcode >> 3) & 0b111  # Destination register code
    immediate_value = fetch_byte()  # Fetch the immediate value from the next byte in RAM

    if ddd == 0b110:  # If destination is M (memory at HL)
        hl_address = get_hl_address()
        ram[hl_address] = immediate_value
    else:
        registers[CODE_TO_INDEX[ddd]] = immediate_value

def lxi(opcode):
    """
    Loads a 16-bit immediate value into a register pair.
    The immediate value is fetched from the next two bytes in RAM (low byte first).
    """
    rp_code = (opcode >> 4) & 0b11  # Register pair code
    low_byte = fetch_byte()         # Fetch the low byte of the immediate value
    high_byte = fetch_byte()        # Fetch the high byte of the immediate value

    value = (high_byte << 8) | low_byte  # Combine high and low bytes to form a 16-bit value

    if rp_code == 0b11:  # If register pair is SP (Stack Pointer)
        global sp
        sp = value & 0xFFFF  # Store the value in the Stack Pointer, ensuring it's 16 bits

    else:
        # Store the immediate value into the specified register pair
        registers[RP_CODE_TO_INDEX[rp_code][1]] = low_byte   # Low byte goes to the first register of the pair
        registers[RP_CODE_TO_INDEX[rp_code][0]] = high_byte  # High byte goes to the second register of the pair

def inx(opcode):
    """
    Increments the value of a register pair or the Stack Pointer by 1.
    """
    rp_code = (opcode >> 4) & 0b11  # Register pair code

    if rp_code == 0b11:  # If register pair is SP (Stack Pointer)
        global sp
        sp = (sp + 1) & 0xFFFF  # Increment SP and wrap around at 16 bits
    else:
        # Increment the specified register pair
        high_index, low_index = RP_CODE_TO_INDEX[rp_code]
        low_byte = registers[low_index]
        high_byte = registers[high_index]

        # Combine high and low bytes to form a 16-bit value, increment it, and split it back into bytes
        value = ((high_byte << 8) | low_byte) + 1
        value &= 0xFFFF  # Ensure it's a 16-bit value

        registers[low_index] = value & 0xFF          # Store the low byte back into the low register
        registers[high_index] = (value >> 8) & 0xFF   # Store the high byte back into the high register

def dcx(opcode):
    """
    Decrements the value of a register pair or the Stack Pointer by 1.
    """
    rp_code = (opcode >> 4) & 0b11  # Register pair code

    if rp_code == 0b11:  # If register pair is SP (Stack Pointer)
        global sp
        sp = (sp - 1) & 0xFFFF  # Decrement SP and wrap around at 16 bits
    else:
        # Decrement the specified register pair
        high_index, low_index = RP_CODE_TO_INDEX[rp_code]
        low_byte = registers[low_index]
        high_byte = registers[high_index]

        # Combine high and low bytes to form a 16-bit value, decrement it, and split it back into bytes
        value = ((high_byte << 8) | low_byte) - 1
        value &= 0xFFFF  # Ensure it's a 16-bit value

        registers[low_index] = value & 0xFF          # Store the low byte back into the low register
        registers[high_index] = (value >> 8) & 0xFF   # Store the high byte back into the high register\

# <-- Arithmetic Operations -->

def add(opcode):
    """
    Adds the values of a source register (or memory address), and register A while storing a carry value and auxiliary carry value in their corresponding flags.
    """
    global flags
    sss = opcode & 0b111 # Source register code
    if sss == 0b110:  # If source is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
    else:
        value = registers[CODE_TO_INDEX[sss]]

    # Perform the addition with the accumulator (register A)
    total = registers[0] + value
    result = total & 0xFF  # Keep only the lower 8 bits

    carry = total > 0xFF  # Check if there was a carry out of the 8-bit range
    aux_carry = ((registers[0] & 0x0F) + (value & 0x0F)) > 0x0F  # Check for auxiliary carry

    registers[0] = result  # Store the result back in the accumulator (register A)

    flags = update_zsp_flags(flags, result)  # Update Zero, Sign, and Parity flags based on the result
    flags = set_or_clear_flag(flags, 0b00000001, carry)  # Update Carry flag (bit 0)
    flags = set_or_clear_flag(flags, 0b00010000, aux_carry) # Update Auxiliary Carry flag (bit 4)

def adc(opcode):
    """
    Adds the values of a source register (or memory address), the carry flag, and register A while storing a carry value and auxiliary carry value in their corresponding flags.
    """
    global flags
    sss = opcode & 0b111 # Source register code
    if sss == 0b110:  # If source is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
    else:
        value = registers[CODE_TO_INDEX[sss]]

    carry_in = flags & 0x01

    # Perform the addition with the accumulator (register A) and carry
    total = registers[0] + value + carry_in
    result = total & 0xFF  # Keep only the lower 8 bits

    carry = total > 0xFF  # Check if there was a carry out of the 8-bit range
    aux_carry = ((registers[0] & 0x0F) + (value & 0x0F) + carry_in) > 0x0F  # Check for auxiliary carry

    registers[0] = result  # Store the result back in the accumulator (register A)

    flags = update_zsp_flags(flags, result)  # Update Zero, Sign, and Parity flags based on the result
    flags = set_or_clear_flag(flags, 0b00000001, carry)  # Update Carry flag (bit 0)
    flags = set_or_clear_flag(flags, 0b00010000, aux_carry) # Update Auxiliary Carry flag (bit 4)

def sub(opcode):
    """
    Adds the values of a source register (or memory address), and register A while storing a carry value and auxiliary carry value in their corresponding flags.
    """
    global flags
    sss = opcode & 0b111 # Source register code
    if sss == 0b110:  # If source is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
    else:
        value = registers[CODE_TO_INDEX[sss]]

    total = registers[0] - value
    result = total & 0xFF # Keep only lower 8 bits

    carry = registers[0] < value # Check if there was a carry out of the 8-bit range
    aux_carry = ((registers[0] & 0x0F) - (value & 0x0F)) < 0 # Check for auxiliary carry

    registers[0] = result  # Store the result back in the accumulator (register A)

    flags = update_zsp_flags(flags, result)  # Update Zero, Sign, and Parity flags based on the result
    flags = set_or_clear_flag(flags, 0b00000001, carry)  # Update Carry flag (bit 0)
    flags = set_or_clear_flag(flags, 0b00010000, aux_carry) # Update Auxiliary Carry flag (bit 4)

def sbb(opcode):
    """
    Subtracts the values of a source register (or memory address), the carry flag, and register A while storing a carry value and auxiliary carry value in their corresponding flags.
    """
    global flags
    sss = opcode & 0b111 # Source register code
    if sss == 0b110:  # If source is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
    else:
        value = registers[CODE_TO_INDEX[sss]]

    borrow_in = flags & 0x01

    # Perform the subtraction with the accumulator (register A) and carry
    total = registers[0] - value - borrow_in
    result = total & 0xFF  # Keep only the lower 8 bits

    carry = total < 0  # Check if there was a carry out of the 8-bit range
    aux_carry = ((registers[0] & 0x0F) - (value & 0x0F) - borrow_in) < 0  # Check for auxiliary carry

    registers[0] = result  # Store the result back in the accumulator (register A)

    flags = update_zsp_flags(flags, result)  # Update Zero, Sign, and Parity flags based on the result
    flags = set_or_clear_flag(flags, 0b00000001, carry)  # Update Carry flag (bit 0)
    flags = set_or_clear_flag(flags, 0b00010000, aux_carry) # Update Auxiliary Carry flag (bit 4)

def ana(opcode):
    """
    Performs a bitwise AND using the values of a source register (or memory address), and register A while storing a carry value and auxiliary carry value in their corresponding flags.
    """
    global flags
    sss = opcode & 0b111 # Source register code
    if sss == 0b110:  # If source is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
    else:
        value = registers[CODE_TO_INDEX[sss]]

    carry = False # carry is always false
    result = registers[0] & value # bitwise and

    aux_carry = ((registers[0] | value) & 0x08) != 0 # bit 3 quirk

    registers[0] = result  # Store the result back in the accumulator (register A)

    flags = update_zsp_flags(flags, result)  # Update Zero, Sign, and Parity flags based on the result
    flags = set_or_clear_flag(flags, 0b00000001, carry)  # Update Carry flag (bit 0)
    flags = set_or_clear_flag(flags, 0b00010000, aux_carry) # Update Auxiliary Carry flag (bit 4)

def xra(opcode):
    """
    Performs a bitwise XOR using the values of a source register (or memory address),  and register A while storing a carry value and auxiliary carry value in their corresponding flags.
    """
    global flags
    sss = opcode & 0b111 # Source register code
    if sss == 0b110:  # If source is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
    else:
        value = registers[CODE_TO_INDEX[sss]]

    
    result = registers[0] ^ value # bitwise XOR

    carry = False # always false
    aux_carry = False # same here

    registers[0] = result  # Store the result back in the accumulator (register A)

    flags = update_zsp_flags(flags, result)  # Update Zero, Sign, and Parity flags based on the result
    flags = set_or_clear_flag(flags, 0b00000001, carry)  # Update Carry flag (bit 0)
    flags = set_or_clear_flag(flags, 0b00010000, aux_carry) # Update Auxiliary Carry flag (bit 4)

def ora(opcode):
    """
    Performs a bitwise OR using the values of a source register (or memory address), the carry flag, and register A while storing a carry value and auxiliary carry value in their corresponding flags.
    """
    global flags
    sss = opcode & 0b111 # Source register code
    if sss == 0b110:  # If source is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
    else:
        value = registers[CODE_TO_INDEX[sss]]

    
    result = registers[0] | value # bitwise OR

    carry = False # always false
    aux_carry = False # same here

    registers[0] = result  # Store the result back in the accumulator (register A)

    flags = update_zsp_flags(flags, result)  # Update Zero, Sign, and Parity flags based on the result
    flags = set_or_clear_flag(flags, 0b00000001, carry)  # Update Carry flag (bit 0)
    flags = set_or_clear_flag(flags, 0b00010000, aux_carry) # Update Auxiliary Carry flag (bit 4)

def cmp(opcode):
    """
    Compares the values of a source register (or memory address), and register A while storing a carry value and auxiliary carry value in their corresponding flags.
    """
    global flags
    sss = opcode & 0b111 # Source register code
    if sss == 0b110:  # If source is M (memory at HL)
        hl_address = get_hl_address()
        value = ram[hl_address]
    else:
        value = registers[CODE_TO_INDEX[sss]]

    total = registers[0] - value
    result = total & 0xFF # Keep only lower 8 bits

    carry = registers[0] < value # Check if there was a carry out of the 8-bit range
    aux_carry = ((registers[0] & 0x0F) - (value & 0x0F)) < 0 # Check for auxiliary carry


    flags = update_zsp_flags(flags, result)  # Update Zero, Sign, and Parity flags based on the result
    flags = set_or_clear_flag(flags, 0b00000001, carry)  # Update Carry flag (bit 0)
    flags = set_or_clear_flag(flags, 0b00010000, aux_carry) # Update Auxiliary Carry flag (bit 4)