"""ForRememberingSettings as a JSON file, by default in the user's state directory."""
import json
import os
import typing

from folio_board.hexagon.driven.for_remembering_settings import ForRememberingSettings, SettingsError
from folio_board.hexagon.driver.for_presenting_drawings import Orientation, Settings


def default_path():
    state = os.environ.get('XDG_STATE_HOME') or os.path.expanduser('~/.local/state')
    return os.path.join(state, 'folio-board', 'settings.json')


class JsonFileSettings(ForRememberingSettings):
    def __init__(self, path=None):
        self.path = path or default_path()

    def remember(self, settings):
        data = {'orientation': settings.orientation, 'pressure_sensitive': settings.pressure_sensitive,
                'shapes': settings.shapes}
        tmp = self.path + '.tmp'
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(tmp, 'w') as out:
                json.dump(data, out)
            os.replace(tmp, self.path)
        except OSError as e:
            raise SettingsError(str(e)) from e

    def recall(self):
        try:
            with open(self.path) as f:
                data = json.load(f)
        except FileNotFoundError:
            return Settings()
        except (OSError, ValueError) as e:
            raise SettingsError(str(e)) from e
        # A setting missing from the file keeps its default.
        if not isinstance(data, dict):
            raise SettingsError(f'unexpected settings in {self.path}')
        default = Settings()
        orientation = data.get('orientation', default.orientation)
        pressure = data.get('pressure_sensitive', default.pressure_sensitive)
        shapes = data.get('shapes', default.shapes)
        if (orientation not in typing.get_args(Orientation) or not isinstance(pressure, bool)
                or not isinstance(shapes, bool)):
            raise SettingsError(f'unexpected settings in {self.path}')
        return Settings(orientation, pressure, shapes)
