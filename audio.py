import numpy as np
import pyaudio
import select
import sys


class Hertz(object):

    def __init__(self, channels=2, duration=5, rate=48000, frequency=40.0):
        self._channels = channels
        self._duration = duration    # in seconds, may be float
        self._rate = rate            # sampling rate, Hz, must be integer
        self._frequency = frequency  # sine frequency, Hz, must be float
        self._p = pyaudio.PyAudio()
        self._stream = None

    def __enter__(self):
        self._generate_stream()
        return self

    def __exit__(self, exception, message, traceback):
        self._stream.stop_stream()
        self._stream.close()
        self._p.terminate()

    def _generate_stream(self):
        pass

    def sound(self):
        pass

    @staticmethod
    def generate(impl):
        if impl is None or impl != 'b':
            print('Generating NonBlocking Stream')
            return NonBlocking()
        else:
            print('Generating Blocking Stream')
            return Blocking()


class Blocking(Hertz):

    def __init__(self, *args, **kwargs):
        super(Blocking, self).__init__(*args, **kwargs)

    def _generate_stream(self):
        self._stream = self._p.open(
            format=pyaudio.paFloat32,
            channels=self._channels,
            rate=self._rate,
            output=True)

    def _generate_sample(self):
        sample_range = self._rate*self._duration*self._channels
        scale = (2/self._channels)*np.pi*(self._frequency/self._rate)
        return (np.sin(np.arange(sample_range)*scale)).astype(np.float32)

    def sound(self):
        sample = self._generate_sample()
        self._stream.write(sample)


class NonBlocking(Hertz):

    def __init__(self, *args, **kwargs):
        super(NonBlocking, self).__init__(*args, **kwargs)
        self._frames_per_buffer = 2048
        self._out_buffer = np.zeros(self._frames_per_buffer * 2).astype(np.float32)
        self._phase = 0

    def _generate_stream(self):
        self._stream = self._p.open(
            format=pyaudio.paFloat32,
            channels=self._channels,
            rate=self._rate,
            frames_per_buffer=self._frames_per_buffer,
            input=False,
            output=True,
            stream_callback=self._callback)

    def _callback(self, in_data, frame_count, time_info, status):
        scale = self._frequency/self._rate
        for n in range(frame_count * self._channels):
            self._out_buffer[n] = np.sin(self._phase)
            self._phase += (2/self._channels)*np.pi*scale
        return self._out_buffer, pyaudio.paContinue

    def _update_frequency(self, new_frequency):
        new_frequency = new_frequency.rstrip('\n')
        self._frequency = float(new_frequency)
        stmt = 'Set frequency to: {new_f} hz\n'.format(new_f=new_frequency)
        print(stmt, end='')

    def sound(self):
        while self._stream.is_active():
            while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                new_frequency = sys.stdin.readline()
                if new_frequency:
                    self._update_frequency(new_frequency)


if __name__ == '__main__':
    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
    with Hertz.generate(arg) as hz:
        hz.sound()
