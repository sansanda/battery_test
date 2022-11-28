import sys
from threading import Timer
import time

def function_to_be_repeated(time_stamp):
    print(time_stamp)


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
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def main() -> int:
    """Echo the input arguments to standard output"""
    rt = RepeatedTimer(1, function_to_be_repeated, time.time())
    rt.start()
    return 0


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit
