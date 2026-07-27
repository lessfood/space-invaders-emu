import cpu, time, os, inout, video, pygame


CYCLES_PER_FRAME = 33333 # How many cpu cycles in a frame?
CYCLES_PER_HALF_FRAME = CYCLES_PER_FRAME//2

FRAME_TIME = 1/60  # seconds per frame, as a float

cycles_since_frame_start = 0
mid_screen_fired = False

import os

def generate_rom(files):
    """
    Generates the Space Invaders ROM by concatenating all four files at runtime
    """
    output_dir = 'roms'
    output_file = os.path.join(output_dir, 'invaders.rom')
    
    # Check if the ROM already exists
    if os.path.exists(output_file):
        print(f"ROM already exists at '{output_file}'. Skipping generation.")
        return
    
    # Ensure the 'roms' directory exists before writing
    os.makedirs(output_dir, exist_ok=True)

    with open(output_file, 'wb') as outfile:
        for filename in files:
            with open(filename, 'rb') as infile:
                outfile.write(infile.read())
    
    print(f"Successfully generated '{output_file}'.")

def load_rom(filepath, mem_location):
    """
    Loads a ROM into memory
    """
    # open the file
    with open(filepath, 'rb') as f: data = f.read()

    # put data in memory
    cpu.ram[mem_location:mem_location + len(data)] = data

    # move program counter
    cpu.pc = mem_location

    print(f"{filepath} loaded at {hex(mem_location)}")

def run_one_frame():
    """
    Runs for one frame of Space Invaders
    """
    global cycles_since_frame_start, mid_screen_fired

    while cycles_since_frame_start < CYCLES_PER_FRAME:
        cpu.step()
        cycles_since_frame_start += 1

        if not mid_screen_fired and cycles_since_frame_start >= CYCLES_PER_HALF_FRAME:
            cpu.request_interrupt(1)
            mid_screen_fired = True

    cpu.request_interrupt(2)
    cycles_since_frame_start = 0
    mid_screen_fired = False



def main():

    cpu.reset_cpu() # reset the cpu

    # register I/O handlers
    cpu.port_in_handlers[1] = inout.read_port1
    cpu.port_in_handlers[2] = inout.read_port2
    cpu.port_in_handlers[3] = inout.read_port3
    
    cpu.port_out_handlers[2] = inout.write_port2
    cpu.port_out_handlers[3] = inout.write_port3  # Add Port 3 OUT
    cpu.port_out_handlers[4] = inout.write_port4
    cpu.port_out_handlers[5] = inout.write_port5  # Add Port 5 OUT

    inout.init_sounds() # Initialize audio here

    # declare files to be loaded
    files = ["roms/invaders.h", "roms/invaders.g", "roms/invaders.f", "roms/invaders.e"]

    generate_rom(files) # generate the rom
    
    load_rom("roms/invaders.rom", 0x0000)

    screen = video.init()

    clock = pygame.time.Clock()

    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            
            # --- Key Pressed ---
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    inout.coin = 1
                elif event.key == pygame.K_1:
                    inout.p1_start = 1
                elif event.key == pygame.K_2:
                    inout.p2_start = 1
                elif event.key == pygame.K_SPACE:
                    inout.p1_shoot = 1
                elif event.key == pygame.K_LEFT:
                    inout.p1_left = 1
                elif event.key == pygame.K_RIGHT:
                    inout.p1_right = 1

            # --- Key Released ---
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_c:
                    inout.coin = 0
                elif event.key == pygame.K_1:
                    inout.p1_start = 0
                elif event.key == pygame.K_2:
                    inout.p2_start = 0
                elif event.key == pygame.K_SPACE:
                    inout.p1_shoot = 0
                elif event.key == pygame.K_LEFT:
                    inout.p1_left = 0
                elif event.key == pygame.K_RIGHT:
                    inout.p1_right = 0

            
        frame_start = time.perf_counter()

        current_fps = clock.get_fps()

        pygame.display.set_caption(f"Space Invaders | FPS: {current_fps:.2f}")

        run_one_frame()

        video.draw_frame(screen, cpu.ram)

        elapsed = time.perf_counter() - frame_start
        sleep_time = FRAME_TIME - elapsed

        if sleep_time > 0:
            time.sleep(sleep_time)

        clock.tick(60)


if __name__ == "__main__":
    main()
