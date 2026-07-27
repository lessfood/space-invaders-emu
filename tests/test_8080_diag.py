"""
General test module for loading in roms to the 8080's memory at a specific location
"""

import sys, os, cpm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cpu

MAX_ITERATIONS = 3000000000

num_cycles = 0

def load_rom(filepath, mem_location):
    # open the file
    with open(filepath, 'rb') as f: data = f.read()

    # put data in memory
    cpu.ram[mem_location:mem_location + len(data)] = data

    # move program counter
    cpu.pc = mem_location

def reset_cpu():

    global num_cycles

    cpu.ram = bytearray(65536)  # 64KB of RAM

    cpu.ports = bytearray(256) # 256 seperate ports for interacting with actual "hardware" (user input)

    cpu.registers = bytearray(7)  # 7 registers: A, B, C, D, E, H, L
    # pairs: b/c, d/e, h/l

    cpu.flags = 0x02 # a single byte (plain int, masked & 0xFF), with bit-level check/set/clear operations at specific positions 
    # (Sign=7, Zero=6, AC=4, Parity=2, Carry=0)
    # 8080 quirk, bit 1 is always on

    cpu.pc = 0x0000  # Program Counter (16-bit); masked & 0xFFFF
    # starts at 0x0000, but can be set to any address in the 64KB address space

    cpu.sp = 0x0000  # Stack Pointer (16-bit); masked & 0xFFFF
    # starts at 0x0000 as a placeholder; real programs initialize SP themselves via LXI SP before using the stack

    cpu.halted = False # Is the CPU halted?

    cpu.interrupts_enabled = False # self-explanatory

    num_cycles = 0 # reset cycles

    print("CPU reset!")

def tst_8080():

    global num_cycles

    last_pcs = []

    while True:
        last_pcs.append(cpu.pc)
        

        if len(last_pcs) > 50:
            last_pcs.pop(0)

        # test rom finished
        if cpu.pc == 0x0000:
            break

        # time to print
        elif cpu.pc == 0x0005:
            cpm.bdos_call()
            continue

        elif num_cycles >= MAX_ITERATIONS:
            for addr in last_pcs:
                print(hex(addr), hex(cpu.ram[addr]))
            raise ValueError(f"""Exceeded max CPU cycles of {MAX_ITERATIONS}\n
            Program counter located at {hex(cpu.pc)}\n
            Register values: {list(cpu.registers)}\n
            Flags: {bin(cpu.flags)}
            Stack pointer: {hex(cpu.sp)}\n
            Last PCs: {[hex(x) for x in last_pcs]}""")



        # count cpu cycles
        num_cycles += 1

        # move cpu forward a cycle
        cpu.step()

if __name__ == "__main__":
    load_rom("tests/TST8080.COM", 0x100)
    tst_8080()
    print("\nTST8080.COM PASSED")

    reset_cpu()

    load_rom("tests/CPUTEST.COM", 0x100)
    tst_8080()
    print("\nCPUTEST.COM PASSED")
    
    reset_cpu()
    
    load_rom("tests/8080PRE.COM", 0x100)
    tst_8080()
    print("\n8080PRE.COM PASSED")
    
    reset_cpu()
    
    load_rom("tests/8080EXER.COM", 0x100)
    tst_8080()
    print("\n8080EXER.COM PASSED")