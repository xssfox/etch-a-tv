import pygame
from pygame.locals import *
import random
import time
from . import modem, rigctl
import pygame_gui
import numpy as np


BANDWIDTH = 2700
BANDWIDTH_GUARD = 200  # the bit in the middle
BANDWIDTH_DEADZONE = 100  # the bits on the side
ZOOM_DIVIDER = 2
TONE_BANDWIDTH = (
    BANDWIDTH - BANDWIDTH_DEADZONE - BANDWIDTH_DEADZONE - BANDWIDTH_GUARD
) / 2
DRAWABLE_SPACE = TONE_BANDWIDTH
TX_OFFSET = BANDWIDTH_DEADZONE
SETTINGS_HEIGHT = 25
swirly_things_draw = []
swirly_things_rx = []

snr = [0 for x in range(25)]


class swirly_thing(pygame.Rect):
    def __init__(self, location):
        self.width = 1
        self.height = 1
        self.center = location
        self.centerx += random.randint(-2, 2)
        self.centery += random.randint(-2, 2)
        self.decay = 250
        self.link_to_last = False

    def update(self):
        self.decay = self.decay - random.randint(0, 1)


def xpos_to_tone(x):
    x = x * ZOOM_DIVIDER
    x = TX_OFFSET + x
    return x


def ypos_to_tone(y):
    y = (y - SETTINGS_HEIGHT) * ZOOM_DIVIDER
    y = TX_OFFSET + TONE_BANDWIDTH + BANDWIDTH_GUARD + y
    return y


threshold = None

should_link = False


def rx_callback(peaks_power_list, fft_data, freq, dbfs, power_nf):
    global should_link, threshold, snr
    link = should_link
    should_link = False
    try:
        db_above_nf = int(max(fft_data) - power_nf)
    except ValueError:
        db_above_nf = 0
    snr.pop(0)
    snr.append(db_above_nf)
    try:
        tones = sorted([peaks_power_list[0], peaks_power_list[1]])
    except IndexError:
        return
    if freq[list(fft_data).index(max(fft_data))] > 3000:
        return
    else:
        try:
            if (
                db_above_nf < threshold.get_current_value()
            ):  # todo make this configurable
                return
        except AttributeError:
            return

    # if freq[fft_data.index(max(fft_data))] > 3000:
    #     return
    x = (tones[0] - TX_OFFSET) / ZOOM_DIVIDER
    y = (
        SETTINGS_HEIGHT
        + (tones[1] - TX_OFFSET - TONE_BANDWIDTH - BANDWIDTH_GUARD) / ZOOM_DIVIDER
    )

    # check if in range
    if tones[0] < TX_OFFSET or tones[0] > TX_OFFSET + TONE_BANDWIDTH:
        return
    if (
        tones[1] < TX_OFFSET + TONE_BANDWIDTH + BANDWIDTH_GUARD
        or tones[1] > TX_OFFSET + TONE_BANDWIDTH + BANDWIDTH_GUARD + TONE_BANDWIDTH
    ):
        return

    location = (x + (DRAWABLE_SPACE / ZOOM_DIVIDER), y)
    swirly = swirly_thing(location)
    swirly.decay = 5 * db_above_nf
    if link == True:
        swirly.link_to_last = True
    swirly_things_rx.append(swirly)
    should_link = True


waterfall_surf = pygame.surface.Surface(
    (int((DRAWABLE_SPACE / ZOOM_DIVIDER) * 2), DRAWABLE_SPACE / ZOOM_DIVIDER)
)


def main():
    # Initialise screen
    global threshold
    pygame.init()

    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(
        (
            int((DRAWABLE_SPACE / ZOOM_DIVIDER) * 2),
            int(DRAWABLE_SPACE / ZOOM_DIVIDER) + SETTINGS_HEIGHT,
        )
    )
    pygame.display.set_caption("Etch A TV")

    tones = modem.Modem(rx_callback)
    cards = [f"[{str(i)}] {x}" for i, x in enumerate(tones.list_audio_devices())]
    in_card = None
    out_card = None
    tones.sineFrequency2 = (
        TX_OFFSET + TONE_BANDWIDTH + (BANDWIDTH_GUARD / 2)
    )  # pilot tone

    manager = pygame_gui.UIManager(
        (
            int((DRAWABLE_SPACE / ZOOM_DIVIDER) * 2),
            int(DRAWABLE_SPACE / ZOOM_DIVIDER) + SETTINGS_HEIGHT,
        )
    )
    threshold = pygame_gui.elements.UIHorizontalSlider(
        relative_rect=pygame.Rect(
            (int(DRAWABLE_SPACE / ZOOM_DIVIDER), 0),
            (int((DRAWABLE_SPACE / ZOOM_DIVIDER)), SETTINGS_HEIGHT),
        ),
        start_value=40,
        value_range=(0, 100),
        manager=manager,
    )
    snd_input = pygame_gui.elements.UIDropDownMenu(
        options_list=["Select Input"] + cards,
        starting_option="Select Input",
        relative_rect=pygame.Rect(
            (0, 0), (int((DRAWABLE_SPACE / ZOOM_DIVIDER) / 2), SETTINGS_HEIGHT)
        ),
        manager=manager,
    )
    snd_output = pygame_gui.elements.UIDropDownMenu(
        options_list=["Select Output"] + cards,
        starting_option="Select Output",
        relative_rect=pygame.Rect(
            (int((DRAWABLE_SPACE / ZOOM_DIVIDER) / 2), 0),
            (int((DRAWABLE_SPACE / ZOOM_DIVIDER) / 2), SETTINGS_HEIGHT),
        ),
        manager=manager,
    )
    try:
        rig = rigctl.Rigctld()
    except ConnectionRefusedError:
        rig = None
        print("Couldn't connect to rigctl so not using it")

    # Event loop
    while 1:
        time_delta = clock.tick(60) / 1000.0
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((255, 242, 255))
        pygame.draw.line(
            background,
            (85, 205, 252),
            (DRAWABLE_SPACE / ZOOM_DIVIDER, 0),
            (
                DRAWABLE_SPACE / ZOOM_DIVIDER,
                (DRAWABLE_SPACE / ZOOM_DIVIDER) + SETTINGS_HEIGHT,
            ),
        )
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                mouse_position = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEBUTTONUP:
                tones.stop()
                if rig:
                    rig.ptt_disable()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if (
                    type(snd_input.current_state)
                    == pygame_gui.elements.ui_drop_down_menu.UIClosedDropDownState
                    and type(snd_output.current_state)
                    == pygame_gui.elements.ui_drop_down_menu.UIClosedDropDownState
                ):
                    mouse_position = pygame.mouse.get_pos()
                    if (
                        mouse_position[0] > SETTINGS_HEIGHT
                        and mouse_position[0]
                        < int(DRAWABLE_SPACE / ZOOM_DIVIDER) + SETTINGS_HEIGHT
                        and mouse_position[1] > 0
                        and mouse_position[1] < int(DRAWABLE_SPACE / ZOOM_DIVIDER)
                    ):
                        tones.sineFrequency = xpos_to_tone(mouse_position[0])
                        tones.sineFrequency1 = ypos_to_tone(mouse_position[1])
                        tones.start()
                        if rig:
                            rig.ptt_enable()
            if pygame.mouse.get_pressed()[0]:
                if (
                    type(snd_input.current_state)
                    == pygame_gui.elements.ui_drop_down_menu.UIClosedDropDownState
                    and type(snd_output.current_state)
                    == pygame_gui.elements.ui_drop_down_menu.UIClosedDropDownState
                ):
                    if (
                        mouse_position[0] > 0
                        and mouse_position[0] < int(DRAWABLE_SPACE / ZOOM_DIVIDER)
                        and mouse_position[1] > SETTINGS_HEIGHT
                        and mouse_position[1]
                        < int(DRAWABLE_SPACE / ZOOM_DIVIDER) + SETTINGS_HEIGHT
                    ):
                        mouse_position = pygame.mouse.get_pos()
                        tones.sineFrequency = xpos_to_tone(mouse_position[0])
                        tones.sineFrequency1 = ypos_to_tone(mouse_position[1])
                        swirly_things_draw.append(swirly_thing((mouse_position)))
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    if event.ui_element == snd_input:
                        if event.text == "Select Input":
                            in_card = None
                        else:
                            in_card = int(event.text.split("]")[0].split("[")[1])
                    if event.ui_element == snd_output:
                        if event.text == "Select Output":
                            out_card = None
                        else:
                            out_card = int(event.text.split("]")[0].split("[")[1])
                    tones.set_cards(in_card, out_card)
            if event.type == QUIT:
                return
            manager.process_events(event)
        manager.update(time_delta)
        for x in swirly_things_draw:
            x.update()
            if x.decay <= 0:
                swirly_things_draw.remove(x)
            else:
                pygame.draw.circle(
                    background, (85, 205, 252), x.center, 1 + (x.decay / 64)
                )
        last_rx = None
        for x in swirly_things_rx:
            x.update()
            if x.decay <= 0:
                try:
                    swirly_things_rx.remove(x)
                except ValueError:
                    pass
            else:
                pygame.draw.circle(
                    background, (85, 205, 252), x.center, 1 + (x.decay / 64)
                )
            if last_rx and x.link_to_last:
                pass
                # pygame.draw.line(background, (85, 205, 252), x.center, last_rx.center,  1+int(x.decay/16))
            last_rx = x
        manager.draw_ui(background)

        snr_value = np.mean(snr)
        # draw the signal level over the top of the bar
        snr_bar_length = int(DRAWABLE_SPACE / ZOOM_DIVIDER) + (
            (((snr_value) / 100) * int((DRAWABLE_SPACE / ZOOM_DIVIDER) * 2)) / 2
        )
        pygame.draw.line(
            background,
            (0, 0, 255),
            (snr_bar_length, 0),
            (int(snr_bar_length), SETTINGS_HEIGHT),
            3,
        )

        screen.blit(background, (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()
