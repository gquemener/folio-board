"""Driven port for keeping the presenter's screen up to date."""


class ForNotifyingThePresenter:
    def page_changed(self) -> None:
        """The page looks different: show it again."""
        raise NotImplementedError

    def status(self, text: str) -> None:
        """Show a lasting line about the pad link or the last save."""
        raise NotImplementedError

    def toast(self, text: str) -> None:
        """Show a short message that goes away by itself."""
        raise NotImplementedError

    def reconnect_available(self, available: bool) -> None:
        """Whether reconnecting makes sense now."""
        raise NotImplementedError
