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

def fetch_byte():
    """
    Fetches a single byte from RAM at the current program counter (PC) address, increments the PC, and returns the byte.
    """
    global pc
    byte = ram[pc]
    pc = (pc + 1) & 0xFFFF  # Increment PC and wrap around at 16 bits
    return byte


# <-- MOV Instruction Family -->

def mov_reg_to_reg(opcode):
    """
    Moves the value from one register to another.
    The opcode format is as follows:
    7 6 5 4 3 2 1 0
    | 0 1 1 1 d d d s s s |
    where ddd is the destination register code and sss is the source register code.
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