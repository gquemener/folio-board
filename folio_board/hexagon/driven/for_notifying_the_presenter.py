"""Driven port for keeping the presenter's screen up to date."""


class ForNotifyingThePresenter:
    def page_changed(self) -> None:
        """The page looks different: show it again."""
        raise NotImplementedError

    def settings_changed(self) -> None:
        """The settings were brought back from the last session: show them on the controls."""
        raise NotImplementedError

    def toast(self, text: str) -> None:
        """Show a short message that goes away by itself, e.g. after saving or when something failed."""
        raise NotImplementedError

    def connection_changed(self, connected: bool) -> None:
        """The pad is connected, or not: show it. Reconnecting only makes sense while it is."""
        raise NotImplementedError
