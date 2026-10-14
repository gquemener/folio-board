"""Driven port for keeping the presenter's screen up to date."""
from typing import Protocol


class ForNotifyingThePresenter(Protocol):
    def page_changed(self) -> None:
        """The page looks different: show it again."""

    def status(self, text: str) -> None:
        """Show a lasting line about the pad link or the last save."""

    def toast(self, text: str) -> None:
        """Show a short message that goes away by itself."""

    def reconnect_available(self, available: bool) -> None:
        """Whether reconnecting makes sense now."""
