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
        self.FRAMESPERBUFFER=1024
        self.OVERLAP = 2 # over lap the FFT for RX.
        #self.RATE=44100
        self.RATE=48000
        self.WIDTH=2

        self.sineFrequency = freq1
        self.sineFrequency1 = freq2
        self.sineFrequency2 = freq3
        self.last_data = []
        for x in range(0,self.OVERLAP):
            self.last_data.append(bytes(2*self.FRAMESPERBUFFER))

        self.callback = callback
        self.window = signal.windows.hann(self.FRAMESPERBUFFER * (self.OVERLAP + 1))

        self.stream = self.p.open(format=self.p.get_format_from_width(self.WIDTH),
                    channels=1, rate=self.RATE, output=True, input=True,
                stream_callback=self.pacallback, frames_per_buffer=self.FRAMESPERBUFFER, input_device_index=3, output_device_index=3 )
        
        self.running = False

        self.fftfreq = np.fft.fftshift(np.fft.fftfreq(self.FRAMESPERBUFFER*(self.OVERLAP + 1))) * self.RATE
        self.fftfreq = self.fftfreq[int(len(self.fftfreq)/2):]

    def pacallback(self, in_data, frame_count, time_info, status):
        raw_buffer = b''.join(self.last_data) + in_data
        data = numpy.frombuffer(raw_buffer, dtype=numpy.int16) * self.window
        data = data.astype(np.float64) / (2 ** 15)
        self.last_data.pop(0)
        self.last_data.append(in_data)
        fft_data = 20 * np.log10(
                abs(np.fft.fftshift(np.fft.fft(data)))
        ) - 20 * np.log10(self.FRAMESPERBUFFER*(self.OVERLAP+ 1))
        fft_data = fft_data[int(len(fft_data)/2):]
        dbfs = 20*np.log10(data.max())
        power_nf = np.mean(fft_data)
        peak_index, dict_vals = signal.find_peaks(fft_data, prominence=10, distance=5)
        #print(peak_index)
        peaks = {self.fftfreq [x]: fft_data[x] for x in peak_index}
        peaks_power_list = sorted(peaks, key=peaks.get, reverse=True)
        self.callback(peaks_power_list, fft_data, self.fftfreq, dbfs, power_nf )

        #  generate output
        outbuf = bytes()
        ampltitude = 65535/2 # because we have three tones
        #frame_count
        if self.running:
            for n in range(frame_count):
                outbuf += int(
                    ampltitude * 0.5 * numpy.sin(self.phase) + 
                    ampltitude * 0.5 * numpy.sin(self.phase1) 
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


