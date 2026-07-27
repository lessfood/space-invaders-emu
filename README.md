# space-invaders-emu
an attempt at making an Intel 8080 Space Invaders emulator in Python!
<br>

## How it works
This project utilizes pygame to render arcade graphics and handle audio playback.

RAM is structured using a `bytearray(0x4000)` (16KB address space) mapping both ROM and Video RAM, alongside a custom 8080 CPU implementation managing accumulator, flags, general-purpose registers, stack pointer, and program counter states.


