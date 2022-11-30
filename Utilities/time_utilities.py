import sys
from threading import Timer, Thread
import time


def function_to_be_repeated():
    suma = 0
    for i in range(1000000):
        suma = suma + i
    print(time.time())


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.function(*self.args, **self.kwargs)
        self.start()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class AccurateRepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.past_time_ref = 0
        self.start()

    def _run(self):
        self.is_running = False
        self.function(*self.args, **self.kwargs)
        self.start()

    def start(self):
        if not self.is_running:
            elapsed_time = time.time() - self.past_time_ref
            if not self.past_time_ref:
                elapsed_time = self.interval  # first time correction
            time_to_subs = elapsed_time - self.interval
            self._timer = Timer(self.interval - time_to_subs, self._run)
            self._timer.start()
            self.past_time_ref = time.time()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class RepeateFunction(object):
    def __init__(self, interval, function, times, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.times = times
        self.args = args
        self.kwargs = kwargs
        self.past_time_ref = 0
        self.elapsed_time = 0
        self.start()

    def start(self):
        for i in range(0, self.times, 1):
            time.sleep(self.interval - self.elapsed_time)
            self.past_time_ref = time.time()
            self.function(*self.args, **self.kwargs)
            self.elapsed_time = time.time() - self.past_time_ref


def main() -> int:
    """Echo the input arguments to standard output"""
    thread = Thread(target=RepeateFunction, args=(1, function_to_be_repeated, 15))
    thread.start()
    return 0


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit