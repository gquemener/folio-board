"""Driven port for the pad: the application asks it to stream pen input, or to stop."""


class PadLinkError(Exception):
    def __init__(self, code: int):
        super().__init__(f'pad link failed ({code})')
        self.code = code


class ForLinkingThePad:
    def start_live(self) -> None:
        """Wait for the pad and stream its pen input; raises PadLinkError if that cannot start."""
        raise NotImplementedError

    def stop_live(self) -> None:
        raise NotImplementedError
