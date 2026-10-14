"""Driver port for the pad: it tells the application what the pen does."""
from typing import Optional, Protocol


class ForReceivingPenInput(Protocol):
    def pen(self, in_range: bool, x: int, y: int, pressure: int) -> None:
        """A pen report: position in pad units and raw pressure, 0 when the pen is lifted."""

    def pad_connected(self, pressure_max: Optional[int]) -> None:
        """The pad is live; pressure_max is its highest pressure, if known."""

    def pad_lost(self, code: int) -> None:
        """The pad's live mode stopped; 0 means on request."""

    def pad_resized(self, width_um: int, height_um: int) -> None:
        """The pad reported its drawing area, in micrometres."""

    def check_connection(self) -> None:
        """Called regularly: waits for the pad again if it has not shown up for a while."""
