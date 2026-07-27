"""
Module for CP/M emulation
"""
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cpu

def bdos_call():

    # read register C
    c = cpu.registers[2]
    d = cpu.registers[3]
    e = cpu.registers[4]

    # print char to console
    if c == 2:
        print(chr(e), end='', flush=False)

    # print $-terminated string at address DE
    elif c == 9:
        # combine bytes
        value = (d << 8) | e

        # walk through ram from value
        for char in cpu.ram[value:]:
            # is char $
            if char == 0x24:
                break

            # print char
            print(chr(char), end='', flush=False)

    # read return address off of stack
    low_byte = cpu.ram[cpu.sp]
    cpu.sp = (cpu.sp + 1) & 0xFFFF
    high_byte = cpu.ram[cpu.sp]
    cpu.sp = (cpu.sp + 1) & 0xFFFF

    # combine the two bytes
    value = (high_byte << 8) | low_byte 

    # return to address
    cpu.pc = value
