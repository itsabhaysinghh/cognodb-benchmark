import time

class Timer:
    def __init__(self):
        self._start_time = None
        self._end_time = None

    def start(self):
        self._start_time = time.perf_counter()
        self._end_time = None
        return self

    def stop(self):
        self._end_time = time.perf_counter()
        return self

    @property
    def elapsed_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        end = self._end_time if self._end_time is not None else time.perf_counter()
        return end - self._start_time

    @property
    def elapsed_ms(self) -> float:
        return self.elapsed_seconds * 1000.0

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
