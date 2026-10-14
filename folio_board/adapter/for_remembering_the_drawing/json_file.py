"""ForRememberingTheDrawing as a JSON file, by default in the user's state directory."""
import json
import os

from folio_board.hexagon.driven.for_remembering_the_drawing import ForRememberingTheDrawing, RememberingError, Stroke


def default_path():
    state = os.environ.get('XDG_STATE_HOME') or os.path.expanduser('~/.local/state')
    return os.path.join(state, 'folio-board', 'drawing.json')


class JsonFileMemory(ForRememberingTheDrawing):
    def __init__(self, path=None):
        self.path = path or default_path()

    def remember(self, strokes):
        data = {'strokes': [{'color': s.color, 'points': [[x, y, round(p, 4)] for x, y, p in s.points]}
                            for s in strokes]}
        tmp = self.path + '.tmp'
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(tmp, 'w') as out:
                json.dump(data, out, separators=(',', ':'))
            os.replace(tmp, self.path)  # a crash while writing leaves the previous drawing whole
        except OSError as e:
            raise RememberingError(str(e)) from e

    def recall(self):
        try:
            with open(self.path) as f:
                data = json.load(f)
            return [Stroke(s['color'], [tuple(p) for p in s['points']]) for s in data['strokes']]
        except FileNotFoundError:
            return []
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise RememberingError(str(e)) from e
