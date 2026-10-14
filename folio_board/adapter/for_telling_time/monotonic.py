"""ForTellingTime with the system's monotonic clock."""
import time

from folio_board.hexagon.driven.for_telling_time import ForTellingTime


class MonotonicClock(ForTellingTime):
    def now(self):
        return time.monotonic()
