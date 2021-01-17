import pygame
from pygame.locals import *
import random
import time 
import modem
import pygame_gui

BANDWIDTH = 2700
BANDWIDTH_GUARD = 200 # the bit in the middle
BANDWIDTH_DEADZONE = 100 # the bits on the side
ZOOM_DIVIDER = 2
TONE_BANDWIDTH = (BANDWIDTH - BANDWIDTH_DEADZONE - BANDWIDTH_DEADZONE - BANDWIDTH_GUARD) /2
DRAWABLE_SPACE = TONE_BANDWIDTH 
TX_OFFSET = BANDWIDTH_DEADZONE
SETTINGS_HEIGHT = 25
swirly_things_draw = []
swirly_things_rx = []

# number of candidates to check 
# CHECK_CANDIDATES = 5
# candidates = []


class swirly_thing(pygame.Rect):
        def __init__(self, location):
            self.width=1
            self.height=1
            self.center=location
            self.centerx+=random.randint(-2, 2)
            self.centery+=random.randint(-2, 2)
            self.decay = 250
            self.link_to_last = False
        def update(self):
            self.decay = self.decay - random.randint(0,1)
def xpos_to_tone(x):
    x = x * ZOOM_DIVIDER
    x = TX_OFFSET + x
    return x

def ypos_to_tone(y):
    y = (y - SETTINGS_HEIGHT) * ZOOM_DIVIDER
    y = TX_OFFSET + TONE_BANDWIDTH + BANDWIDTH_GUARD +  y
    return y
threshold = None

should_link = False

def rx_callback(peaks_power_list, fft_data, freq, dbfs, power_nf):
    global should_link, threshold
    link = should_link
    should_link = False
    try:
        tones = sorted([peaks_power_list[0], peaks_power_list[1]])
    except IndexError:
        return
    if freq[list(fft_data).index(max(fft_data))] > 3000: 
        return
    else:
        
        db_above_nf = int(max(fft_data) - power_nf)
        print(db_above_nf)
        try:
            if db_above_nf < threshold.get_current_value(): # todo make this configurable
                return
        except AttributeError:
            return
    
        
    # if freq[fft_data.index(max(fft_data))] > 3000:
    #     return
    x= (tones[0]- TX_OFFSET)/ ZOOM_DIVIDER
    y= SETTINGS_HEIGHT + (tones[1]  - TX_OFFSET - TONE_BANDWIDTH  - BANDWIDTH_GUARD ) / ZOOM_DIVIDER

    # check if in range
    if tones[0] < TX_OFFSET or tones[0] > TX_OFFSET + TONE_BANDWIDTH:
        return
    if tones[1] < TX_OFFSET + TONE_BANDWIDTH + BANDWIDTH_GUARD or tones[1]  > TX_OFFSET + TONE_BANDWIDTH + BANDWIDTH_GUARD + TONE_BANDWIDTH:
        return
    
    location = (x+ (DRAWABLE_SPACE/ZOOM_DIVIDER),y)
    swirly = swirly_thing(location)
    swirly.decay = 5*db_above_nf
    if link == True:
        swirly.link_to_last = True
    swirly_things_rx.append(swirly)
    should_link = True

    
waterfall_surf = pygame.surface.Surface((int((DRAWABLE_SPACE/ZOOM_DIVIDER)*2), DRAWABLE_SPACE / ZOOM_DIVIDER))



def main():
    # Initialise screen
    global threshold
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((int((DRAWABLE_SPACE/ZOOM_DIVIDER)*2), int(DRAWABLE_SPACE/ZOOM_DIVIDER) + SETTINGS_HEIGHT))
    pygame.display.set_caption('Etch A TV')

    tones = modem.Modem(rx_callback)
    tones.sineFrequency2 = TX_OFFSET + TONE_BANDWIDTH + (BANDWIDTH_GUARD/2) # pilot tone

    manager = pygame_gui.UIManager((int((DRAWABLE_SPACE/ZOOM_DIVIDER)*2), int(DRAWABLE_SPACE/ZOOM_DIVIDER) + SETTINGS_HEIGHT))
    threshold = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect((0, 0), (int((DRAWABLE_SPACE/ZOOM_DIVIDER)*2), SETTINGS_HEIGHT)),
                                             start_value=40, value_range=(0,100),
                                             manager=manager)

    # Event loop
    while 1:
        time_delta = clock.tick(60)/1000.0
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
            manager.process_events(event)
        manager.update(time_delta)
        for x in swirly_things_draw:
            x.update()
            if x.decay <= 0:
                swirly_things_draw.remove(x)
            else:
                pygame.draw.circle(background, (85, 205, 252), x.center, 1+(x.decay/64))
        last_rx = None
        for x in swirly_things_rx:
            x.update()
            if x.decay <= 0:
                try:
                    swirly_things_rx.remove(x)
                except ValueError:
                    pass
            else:
                pygame.draw.circle(background, (85, 205, 252), x.center, 1+(x.decay/64))
            if last_rx and x.link_to_last:
                pass
                #pygame.draw.line(background, (85, 205, 252), x.center, last_rx.center,  1+int(x.decay/16))
            last_rx = x
        manager.draw_ui(background)
        screen.blit(background, (0, 0))
        pygame.display.flip()
        


if __name__ == '__main__': main()