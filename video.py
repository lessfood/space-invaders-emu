# video.py
import pygame

WIDTH, HEIGHT = 224, 256
SCALE = 2

def init():
    pygame.init()
    # SCALED flag tells pygame to let the OS/GPU handle the upscaling
    screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE), pygame.SCALED)
    pygame.display.set_caption("Space Invaders")
    large_icon = pygame.image.load('assets/icon.png')
    small_icon = pygame.transform.smoothscale(large_icon, (32, 32))
    pygame.display.set_icon(small_icon)
    print("Screen initalized")
    return screen

def draw_frame(screen, ram):
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill((0, 0, 0))
    
    # Lock the surface for direct, high-speed pixel memory access
    pixels = pygame.PixelArray(surface)
    white = surface.map_rgb((255, 255, 255))

    for byte_index in range(0x2400, 0x4000):
        byte = ram[byte_index]
        
        # Massive optimization: skip empty space (0x00)
        if not byte:
            continue

        offset = byte_index - 0x2400
        col = offset // 32
        row_group = offset % 32

        # Only process bits if the byte actually has lit pixels
        for bit in range(8):
            if byte & (1 << bit):
                x = col
                y = 255 - (row_group * 8 + bit)
                pixels[x, y] = white

    # You must close/delete the PixelArray before blitting the surface
    pixels.close()

    scaled = pygame.transform.scale(surface, (WIDTH * SCALE, HEIGHT * SCALE))
    screen.blit(scaled, (0, 0))
    pygame.display.flip()