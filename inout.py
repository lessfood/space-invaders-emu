import pygame
# --- Port 1: Player 1 controls ---
# bit 0: coin slot
# bit 1: P2 start button
# bit 2: P1 start button
# bit 3: unused (always 1)
# bit 4: P1 fire
# bit 5: P1 left
# bit 6: P1 right
# bit 7: unused (always 1)

port1_state = 0x88  # 0b10001000


# --- Shift register hardware ---

shift_register = 0x0000
shift_amount = 0          # how far to shift on read (0-7), set via port 2 out

# --- Player 1 & System States ---
coin = 0
p1_start = 0
p2_start = 0
p1_shoot = 0
p1_left = 0
p1_right = 0

def read_port1():
    res = 0
    res |= (coin << 0)       # Bit 0: Coin
    res |= (p2_start << 1)   # Bit 1: P2 Start
    res |= (p1_start << 2)   # Bit 2: P1 Start
    res |= (1 << 3)          # Bit 3: Always 1
    res |= (p1_shoot << 4)   # Bit 4: P1 Shoot
    res |= (p1_left << 5)    # Bit 5: P1 Left
    res |= (p1_right << 6)   # Bit 6: P1 Right
    return res


# --- Player 2 States ---
p2_shoot = 0
p2_left = 0
p2_right = 0

def read_port2():
    res = 0
    # Bits 0, 1: Lives (00 = 3 lives)
    # Bit 2: Tilt (0 = normal)
    # Bit 3: Extra life at 1500 (0 = 1500, 1 = 1000)
    # Bit 7: Coin info displayed on demo screen (0 = ON)
    
    res |= (p2_shoot << 4)   # Bit 4: P2 Shoot
    res |= (p2_left << 5)    # Bit 5: P2 Left
    res |= (p2_right << 6)   # Bit 6: P2 Right
    return res

def write_port2(byte):
    global shift_amount

    shift_amount = byte & 0x7 # masked with 0b0111

def write_port4(byte):
    global shift_register

    # shift byte
    written_byte = byte << 8

    # write to register
    shift_register = ((shift_register >> 8) | written_byte) & 0xFFFF

def read_port3():
    #if shift_amount == 0:
        # upper 8 bits
    #    return (shift_register >> 8) & 0xFF
    
    return ((shift_register >> (8 - shift_amount)) & 0xFF)

# --- Sound Implementation ---
sounds = {}
ufo_channel = None

last_port3 = 0
last_port5 = 0

def init_sounds():
    global ufo_channel
    pygame.mixer.init()
    
    # Load all sound assets
    sounds['shoot'] = pygame.mixer.Sound('sounds/shoot.wav')
    sounds['player_die'] = pygame.mixer.Sound('sounds/explosion.wav')
    sounds['invader_die'] = pygame.mixer.Sound('sounds/invaderkilled.wav')
    sounds['fleet1'] = pygame.mixer.Sound('sounds/fastinvader1.wav')
    sounds['fleet2'] = pygame.mixer.Sound('sounds/fastinvader2.wav')
    sounds['fleet3'] = pygame.mixer.Sound('sounds/fastinvader3.wav')
    sounds['fleet4'] = pygame.mixer.Sound('sounds/fastinvader4.wav')
    sounds['ufo'] = pygame.mixer.Sound('sounds/ufo_lowpitch.wav')
    sounds['ufo_hit'] = pygame.mixer.Sound('sounds/ufo_highpitch.wav')
    sounds['extra_ship'] = pygame.mixer.Sound('sounds/extra_ship.wav')
    
    # Reserve a channel specifically for the looping UFO sound
    ufo_channel = pygame.mixer.Channel(0)

def write_port3(val):
    global last_port3
    # Rising edge: active now, but wasn't active last time
    rising_edge = val & ~last_port3
    # Falling edge: inactive now, but was active last time
    falling_edge = ~val & last_port3
    
    # UFO is special: it loops as long as the bit is high
    if rising_edge & 0x01: 
        ufo_channel.play(sounds['ufo'], loops=-1)
    if falling_edge & 0x01: 
        ufo_channel.stop()
        
    if rising_edge & 0x02: sounds['shoot'].play()
    if rising_edge & 0x04: sounds['player_die'].play()
    if rising_edge & 0x08: sounds['invader_die'].play()
    if rising_edge & 0x10: sounds['extra_ship'].play()

    last_port3 = val

def write_port5(val):
    global last_port5
    rising_edge = val & ~last_port5
    
    if rising_edge & 0x01: sounds['fleet1'].play()
    if rising_edge & 0x02: sounds['fleet2'].play()
    if rising_edge & 0x04: sounds['fleet3'].play()
    if rising_edge & 0x08: sounds['fleet4'].play()
    if rising_edge & 0x10: sounds['ufo_hit'].play()
    
    last_port5 = val