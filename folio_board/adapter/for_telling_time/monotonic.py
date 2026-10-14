"""ForTellingTime with the system's monotonic clock."""
import time


class MonotonicClock:
    def now(self):
        return time.monotonic()
