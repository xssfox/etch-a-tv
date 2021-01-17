import pygame
from pygame.locals import *
import random
import time 
import modem

BANDWIDTH = 2700
BANDWIDTH_GUARD = 50 # the bit in the middle
BANDWIDTH_DEADZONE = 100 # the bits on the side
ZOOM_DIVIDER = 2
TONE_BANDWIDTH = (BANDWIDTH - BANDWIDTH_DEADZONE - BANDWIDTH_DEADZONE - BANDWIDTH_GUARD) /2
DRAWABLE_SPACE = TONE_BANDWIDTH 
TX_OFFSET = BANDWIDTH_DEADZONE

swirly_things_draw = []
swirly_things_rx = []


class swirly_thing(pygame.Rect):
        def __init__(self, location):
            self.width=1
            self.height=1
            self.center=location
            self.centerx+=random.randint(-2, 2)
            self.centery+=random.randint(-2, 2)
            self.opacity = random.randint(100,255)
        def update(self):
            self.opacity = self.opacity - random.randint(0,1)
def xpos_to_tone(x):
    x = x * ZOOM_DIVIDER
    x = TX_OFFSET + x
    return x

def ypos_to_tone(y):
    y = y * ZOOM_DIVIDER
    y = TX_OFFSET + TONE_BANDWIDTH + BANDWIDTH_GUARD +  y
    return y

def rx_callback(peaks_power_list, fft_data, freq):
    try:
        tones = sorted([peaks_power_list[0], peaks_power_list[1]])
        x= (tones[0]- TX_OFFSET)/ ZOOM_DIVIDER
        y= (tones[1]  - TX_OFFSET - TONE_BANDWIDTH  - BANDWIDTH_GUARD ) / ZOOM_DIVIDER
        location = (x+ (DRAWABLE_SPACE/ZOOM_DIVIDER),y )
        print(location)
        swirly_things_rx.append(swirly_thing(location))
    except:
        pass
    
    #print(peaks_power_list)
    # check if we even have peaks in our desired range
    # find drawable x / y from freq
    # swirly_things_rx.append(swirly_thing((mouse_position)))
    
def main():
    # Initialise screen
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((int(DRAWABLE_SPACE), int(DRAWABLE_SPACE/ZOOM_DIVIDER)))
    pygame.display.set_caption('Etch A TV')

    tones = modem.Modem(rx_callback)
    tones.sineFrequency2 = TX_OFFSET + TONE_BANDWIDTH + (BANDWIDTH_GUARD/2) # pilot tone

    # Event loop
    while 1:
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((255, 242, 255))
        pygame.draw.line(background, (85, 205, 252), (DRAWABLE_SPACE/ZOOM_DIVIDER,0), (DRAWABLE_SPACE/ZOOM_DIVIDER,DRAWABLE_SPACE/ZOOM_DIVIDER))
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                mouse_position = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONUP:
                tones.stop()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_position = pygame.mouse.get_pos()
                tones.sineFrequency = xpos_to_tone(mouse_position[0])
                tones.sineFrequency1 = ypos_to_tone(mouse_position[1])
                tones.start()
            if pygame.mouse.get_pressed()[0]:
                mouse_position = pygame.mouse.get_pos()
                tones.sineFrequency = xpos_to_tone(mouse_position[0])
                tones.sineFrequency1 = ypos_to_tone(mouse_position[1])
                swirly_things_draw.append(swirly_thing((mouse_position)))
            if event.type == QUIT:
                return
        for x in swirly_things_draw:
            x.update()
            if x.opacity <= 0:
                swirly_things_draw.remove(x)
            else:
                pygame.draw.circle(background, (85, 205, 252), x.center, x.opacity/64)
        for x in swirly_things_rx:
            x.update()
            if x.opacity <= 0:
                try:
                    swirly_things_draw.remove(x)
                except ValueError:
                    pass
            else:
                pygame.draw.circle(background, (85, 205, 252), x.center, x.opacity/64)
        screen.blit(background, (0, 0))
        pygame.display.flip()
        clock.tick(50)


if __name__ == '__main__': main()