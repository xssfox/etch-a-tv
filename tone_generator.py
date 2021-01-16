import numpy
import pyaudio
import math
import random
import time

class modulate():
    def __init__(self, freq1=440, freq2=480):
        self.phase=0
        self.phase1=0
        self.FRAMESPERBUFFER=1024
        self.RATE=44100
        self.WIDTH=2

        self.sineFrequency = freq1
        self.sineFrequency1 = freq2

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.p.get_format_from_width(self.WIDTH),
                    channels=1, rate=self.RATE, output=4,
                stream_callback=self.pacallback, frames_per_buffer=self.FRAMESPERBUFFER)
        
        self.running = False

    def pacallback(self, in_data, frame_count, time_info, status):
        # print(frame_count)
        # print(phase)
        outbuf = bytes()
        ampltitude = 32767/2 # because we have two tones
        #frame_count
        if self.running:
            for n in range(frame_count):
                outbuf += int(ampltitude * 0.5 * numpy.sin(self.phase) + ampltitude * 0.5 * numpy.sin(self.phase1)).to_bytes(2, byteorder='little', signed=True)
                self.phase += 2*numpy.pi*self.sineFrequency/self.RATE
                self.phase1 += 2*numpy.pi*self.sineFrequency1/self.RATE
        else:
            outbuf = bytes(2*frame_count)

        return (outbuf,pyaudio.paContinue)

    def start(self):
        self.running = True
    def stop(self):
        self.running = False

if __name__ == '__main__':
    a = modulate()
    a.start()
    while 1:
        time.sleep(0.01)
        print(a.sineFrequency)
        a.sineFrequency += 1
        if a.sineFrequency > 480:
            a.stop()
        if a.sineFrequency > 560:
            a.start()
