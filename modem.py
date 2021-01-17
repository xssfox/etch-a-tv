import numpy
import pyaudio
import math
import random
import time
from scipy import signal
import numpy as np
from scipy.fft import fft, fftfreq, rfft

class Modem():
    def __init__(self, callback, freq1=440, freq2=480, freq3=500):
        self.p = pyaudio.PyAudio()
        self.phase=0
        self.phase1=0
        self.phase2=0 # alignment
        self.FRAMESPERBUFFER=4096
        #self.RATE=44100
        self.RATE=48000
        self.WIDTH=2

        self.sineFrequency = freq1
        self.sineFrequency1 = freq2
        self.sineFrequency2 = freq3

        self.callback = callback
        self.window = signal.windows.hann(self.FRAMESPERBUFFER)

        self.stream = self.p.open(format=self.p.get_format_from_width(self.WIDTH),
                    channels=1, rate=self.RATE, output=True, input=True,
                stream_callback=self.pacallback, frames_per_buffer=self.FRAMESPERBUFFER, input_device_index=5, output_device_index=6 )
        
        self.running = False

    def pacallback(self, in_data, frame_count, time_info, status):
        data = numpy.frombuffer(in_data, dtype=numpy.int16) * self.window
        fft_data = 20 * np.log10(abs(np.fft.fft(data).real)) - 20 * np.log10(self.FRAMESPERBUFFER)
        fft_data = fft_data[:int(len(fft_data)/2)] 
        freq = np.fft.fftfreq(self.FRAMESPERBUFFER,1.0/self.RATE)
        freq = freq[:int(len(freq)/2)]
        peak_index, dict_vals = signal.find_peaks(fft_data, prominence=20, distance=50)
        peaks = {freq[x]: fft_data[x] for x in peak_index}
        peaks_power_list = sorted(peaks, key=peaks.get, reverse=True)
        self.callback(peaks_power_list, fft_data, freq)

        #  generate output
        outbuf = bytes()
        ampltitude = 32767/3 # because we have three tones
        #frame_count
        if self.running:
            for n in range(frame_count):
                outbuf += int(
                    ampltitude * 0.3 * numpy.sin(self.phase) + 
                    ampltitude * 0.3 * numpy.sin(self.phase1) +
                    ampltitude * 0.3 * numpy.sin(self.phase2) 
                ).to_bytes(2, byteorder='little', signed=True)
                self.phase += 2*numpy.pi*self.sineFrequency/self.RATE
                self.phase1 += 2*numpy.pi*self.sineFrequency1/self.RATE
                self.phase2 += 2*numpy.pi*self.sineFrequency2/self.RATE

        else:
            outbuf = bytes(2*frame_count)
        return (outbuf,pyaudio.paContinue)

    def start(self):
        self.running = True
    def stop(self):
        self.running = False


