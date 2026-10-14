"""ForRememberingTheDrawing as a JSON file, by default in the user's state directory."""
import json
import os

from folio_board.hexagon.driven.for_remembering_the_drawing import (Arrow, Box, Ellipse, ForRememberingTheDrawing,
                                                                    RememberingError, Stroke)

VERSION = 2


def default_path():
    state = os.environ.get('XDG_STATE_HOME') or os.path.expanduser('~/.local/state')
    return os.path.join(state, 'folio-board', 'drawing.json')


class JsonFileMemory(ForRememberingTheDrawing):
    def __init__(self, path=None):
        self.path = path or default_path()

    def remember(self, items):
        data = {'version': VERSION, 'items': [encode(item) for item in items]}
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
            return [decode(item) for item in data['items']]
        except FileNotFoundError:
            return []
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise RememberingError(str(e)) from e


def encode(item):
    if isinstance(item, Stroke):
        return {'type': 'stroke', **encode_stroke(item)}
    shape = {'color': item.color, 'pressure': round(item.pressure, 4),
             'strokes': [encode_stroke(s) for s in item.strokes]}
    if isinstance(item, Box):
        return {'type': 'box', 'rect': [round(n) for n in item.rect], **shape}
    if isinstance(item, Ellipse):
        return {'type': 'ellipse', 'center': [round(n) for n in item.center],
                'radii': [round(n) for n in item.radii], **shape}
    return {'type': 'arrow', 'tail': [round(n) for n in item.tail], 'control': [round(n) for n in item.control],
            'tip': [round(n) for n in item.tip], **shape}


def encode_stroke(stroke):
    return {'color': stroke.color, 'points': [[x, y, round(p, 4)] for x, y, p in stroke.points]}


def decode(data):
    kind = data['type']
    if kind == 'stroke':
        return decode_stroke(data)
    strokes = [decode_stroke(s) for s in data['strokes']]
    if kind == 'box':
        return Box(data['color'], data['pressure'], tuple(data['rect']), strokes)
    if kind == 'ellipse':
        return Ellipse(data['color'], data['pressure'], tuple(data['center']), tuple(data['radii']), strokes)
    if kind == 'arrow':
        return Arrow(data['color'], data['pressure'], tuple(data['tail']), tuple(data['control']),
                     tuple(data['tip']), strokes)
    raise ValueError(f'unknown item type {kind!r}')


def decode_stroke(data):
    return Stroke(data['color'], [tuple(p) for p in data['points']])
