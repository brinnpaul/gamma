import numpy as np
import pyaudio
import select
import array
import sys


class Hertz(object):

    def __init__(self, volume=0.5, duration=5, rate=44100, frequency=40.0):
        self._duration=duration   # in seconds, may be float
        self._rate=rate           # sampling rate, Hz, must be integer
        self._frequency=frequency # sine frequency, Hz, must be float
        self._p = pyaudio.PyAudio()
        self._stream = None

    def __enter__(self):
        self._generate_stream()
        return self

    def __exit__(self, exception, message, traceback):
        self._stream.stop_stream()
        self._stream.close()
        self._p.terminate()

    def _stream(self):
        pass

    def sound(self):
        pass

    @staticmethod
    def generate(type):
        if type is None or type != 'b':
            print('Generating NonBlocking Stream')
            return NonBlocking()
        else:
            print('Generating Blocking Stream')
            return Blocking()


class Blocking(Hertz):

    def __init__(self, *args, **kwargs):
        super(Blocking, self).__init__(kwargs) # python black magic

    def _generate_stream(self):
        self._stream = self._p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self._rate,
            output=True)

    def _generate_sample(self):
        raw_sample = self._rate*self._duration
        scale = self._frequency/self._rate
        return (np.sin(2*np.pi*np.arange(raw_sample)*scale)).astype(np.float32)

    def sound(self):
        sample = self._generate_sample()
        self._stream.write(sample)


class NonBlocking(Hertz):

    def __init__(self, *args, **kwargs):
        super(NonBlocking, self).__init__(kwargs) # python black magic
        self._frames_per_buffer = 2048
        self._outbuf = array.array('f',range(self._frames_per_buffer))
        self._phase = 0

    def _generate_stream(self):
        self._stream = self._p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self._rate,
            frames_per_buffer=self._frames_per_buffer,
            input=False,
            output=True,
            stream_callback=self._callback)

    def _callback(self, in_data, frame_count, time_info, status):
        for n in range(frame_count):
            self._outbuf[n] = np.sin(self._phase)
            self._phase += 2*np.pi*self._frequency/self._rate

        return (np.array(self._outbuf).astype(np.float32),pyaudio.paContinue)

    def _update_frequency(self, new_frequency):
        new_frequency = new_frequency.rstrip('\n')
        self._frequency = float(new_frequency)
        stmt = 'Set new frequency to: {new_f} hz\n'.format(new_f=new_frequency)
        print(stmt, end='')

    def sound(self):
        while self._stream.is_active():
            while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
              new_f = sys.stdin.readline()
              if new_f:
                self._update_frequency(new_f)


if __name__ == '__main__':
    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
    with Hertz.generate(arg) as hz:
        hz.sound()
