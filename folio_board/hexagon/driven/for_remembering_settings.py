"""Driven port for keeping the presenter's settings from one session to the next."""
from folio_board.hexagon.driver.for_presenting_drawings import Settings


class SettingsError(Exception):
    pass


class ForRememberingSettings:
    def remember(self, settings: Settings) -> None:
        """Keep these settings in place of the ones kept before; raises SettingsError."""
        raise NotImplementedError

    def recall(self) -> Settings:
        """The settings kept last, or the default ones if none were kept; raises SettingsError."""
        raise NotImplementedError
