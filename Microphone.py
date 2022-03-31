import datetime
import logging
import os

from contextlib import contextmanager
from ctypes import *
import pyaudio
import wave

# Error handler code to supress non-relevant warnings
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)

class Microphone(object):
    # Class to control rPi HQ camera
    def __init__(self, recordTime, baseLog):
        self.errorRecord = 0
        self.errorSaving = 0

        self.form_1 = pyaudio.paInt16 # 16-bit resolution
        self.chans = 1 # 1 channel
        self.samp_rate = 44100 # 44.1kHz sampling rate
        self.chunk = 4096 # 2^12 samples for buffer
        self.recordTime = recordTime # seconds to record

        # TODO: get the index dynamically based on the Mic_Init
        self.dev_index = 2 # device index found by p.get_device_info_by_index(ii)

        # Create the sound log folder if not exists
        self.soundPath = baseLog + '/SoundLog'
        if not os.path.exists(self.soundPath):
            os.makedirs(self.soundPath)

        try:
            with noalsaerr():
                self.audio = pyaudio.PyAudio() # create pyaudio instantiation
        except:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': USB mic initialization failure.')

    def __del__(self):
        try:
            self.audio.terminate()
        except:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': USB mic reference closing failure.')

    def record(self):
        frames = []

        try:
            # Create pyaudio stream
            stream = self.audio.open(format = self.form_1,rate = self.samp_rate,channels = self.chans, \
                                input_device_index = self.dev_index,input = True, \
                                frames_per_buffer = self.chunk)

            # Loop through stream and append audio chunks to frame array
            for ii in range(0,int((self.samp_rate/self.chunk)*self.recordTime)):
                data = stream.read(self.chunk)
                frames.append(data)

            # Stop the stream and close it
            stream.stop_stream()
            stream.close()

            self.errorRecord = 0
        except:
            if self.errorRecord == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': USB mic recording failure.')
                self.errorRecord = 1

        # Generate the .waw file name
        now = datetime.datetime.now()
        timeStamp = now.strftime("%y%m%d_%H%M%S")
        wav_output_filename = self.soundPath + '/' + timeStamp + '.wav'

        try:
            # Save the audio frames as .wav file
            wavefile = wave.open(wav_output_filename,'wb')
            wavefile.setnchannels(self.chans)
            wavefile.setsampwidth(self.audio.get_sample_size(self.form_1))
            wavefile.setframerate(self.samp_rate)
            wavefile.writeframes(b''.join(frames))
            wavefile.close()

            logging.info(timeStamp + ': Sound data were writen to the log.')
            self.errorSaving = 0
        except:
            if self.errorRecord == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': Sound data saving failure.')
                self.errorRecord = 1