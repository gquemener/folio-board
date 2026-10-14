# folio-board

Mirror what you draw on a Wacom SmartPad (Bamboo Folio, Bamboo Slate, Bamboo
Spark, Intuos Paper) into a desktop window, live. Share that window in a video
call and remote coworkers watch your sketch as you draw it on paper.

It drives [Tuhi](https://github.com/tuhiproject/tuhi)'s live mode, but instead
of turning the pad into a system tablet (which hijacks your mouse cursor), it
draws the strokes in its own window. No root access needed.

## Requirements

- Linux with Bluetooth (BlueZ)
- [Tuhi](https://github.com/tuhiproject/tuhi), with your pad registered once
- Python 3 with PyGObject, pycairo and GTK 4 (GLib ≥ 2.80)

## Installation

### 1. Install Tuhi and the Python dependencies

Arch Linux:

```sh
yay -S tuhi-git            # or any AUR helper
sudo pacman -S python-gobject python-cairo gtk4
```

Fedora:

```sh
sudo dnf install tuhi python3-gobject python3-cairo gtk4
```

Debian / Ubuntu (Tuhi is not packaged, install it
[from source](https://github.com/tuhiproject/tuhi#installation)):

```sh
sudo apt install python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-4.0
```

### 2. Register your pad with Tuhi (once)

Start the Tuhi app (`tuhi`), hold the pad's button until the LED blinks blue,
and follow the registration steps. You can close Tuhi afterwards.

### 3. Install folio-board

```sh
git clone https://github.com/<you>/folio-board.git
ln -s "$PWD/folio-board/folio-board" ~/.local/bin/folio-board
```

Make sure `~/.local/bin` is in your `PATH`. The `folio-board` script loads the
`folio_board` package next to it, so link it rather than copying it, and keep
the clone in place.

## Usage

```sh
folio-board                      # uses the first pad registered in Tuhi
folio-board DF:87:C0:AB:82:6D    # or pick a pad by Bluetooth address
```

1. Run `folio-board`. It starts the Tuhi daemon if it isn't already running.
2. Press the pad's button. The header shows **Connected, draw away**.
3. Draw on the pad. Share the **Folio board** window in your call.

While waiting, the window retries the connection every 30 seconds, so you can
press the pad's button at any time.

| Action                      | Button                          | Key        |
| --------------------------- | ------------------------------- | ---------- |
| Clear the page (asks first) | Clear                           | `c`        |
| Portrait / landscape        | Portrait, Landscape             | `r`        |
| Pressure on/off             | Pressure                        | `p`        |
| Shapes on/off               | Shapes                          | `o`        |
| Pen color                   |                                 | `&` to `ç` |
| Save as PNG or SVG          | Save                            | `Ctrl+S`   |
| Copy as SVG                 | Copy                            | `Ctrl+C`   |
| Pick area to save or copy   | drag with the mouse on the page |            |
| Force a reconnect           | Reconnect                       |            |
| Quit                        |                                 | `q`, `Esc` |

The drawing is kept between sessions: close the window, and the next
`folio-board` shows the page as you left it. It stays until you clear it.
**Clear** asks for confirmation first, since a cleared drawing cannot be
brought back.

With **Pressure** checked (the default), pressing harder draws a thicker line.
Uncheck it to draw every stroke at the same width.

The orientation and the **Pressure** and **Shapes** settings are kept between
sessions too, and clearing the drawing leaves them as they are.

### Shapes

With **Shapes** checked (the default), boxes, circles and arrows you draw by
hand are replaced by clean ones, with a slightly sketchy, mockup-like look. They keep
the color you drew them in, and their line width follows the **Pressure**
setting, like strokes do. Uncheck **Shapes** when you want to draw freely:
what you draw from then on stays as drawn, and shapes already on the page stay.

- **Boxes** can be drawn in one stroke or in up to four (a side or an L at a
  time). They come out upright, so a box tilted more than about 15° stays as
  drawn, and the shorter side must be at least 8 mm, so handwriting never snaps.
- **Circles** and ellipses, usually drawn in one stroke, must go almost all the
  way round, so a U or an arc stays as drawn. One that is nearly round, its
  width and height within 20% of each other, becomes a perfect circle; a
  flatter one stays an upright ellipse. Like boxes, they are at least 8 mm
  across.
- **Arrows** are a shaft followed by a head, drawn as a V or as two strokes.
  A curved shaft gives a curved arrow; a nearly straight one gives a straight
  arrow, turned to the nearest horizontal, vertical or diagonal when close.

Strokes count as one shape when you draw them one right after another, with
less than 1.5 s between them, in the same color. Pause a little before
drawing next to a shape you have just finished, so the two don't get mixed.
The shape appears as soon as its last stroke is done.

### Colors

Press a key of the top row of a French (AZERTY) keyboard, without Shift, to
draw the next strokes in another color:

| Key | Color  | Key | Color  | Key | Color |
| --- | ------ | --- | ------ | --- | ----- |
| `&` | Black  | `'` | Green  | `è` | Lilac |
| `é` | Orange | `(` | Yellow | `_` | Pink  |
| `"` | Blue   | `-` | Red    | `ç` | Brown |

The window briefly names the color you picked, and the header shows the
current one. Each session starts in black, and strokes keep the color they
were drawn in. `à`, the next key, does nothing for now.

The red dot shows where the pen hovers, so viewers can follow it before it
touches the paper.

Save opens a file dialog in your Pictures folder. The format follows the file
extension: `.svg` gives a vector file at the paper's real size, anything else a
200 DPI PNG. The saved page uses the board's current orientation and leaves out
the hover dot.

To save only part of the page, drag a rectangle over it with the mouse first:
the rest is shaded and Save keeps only the framed area. Drag again to change it,
or click outside the framed area to go back to using the whole page. Switching
between portrait and landscape drops the crop.

Copy puts the same page, or the framed area, on the clipboard as SVG, ready to
paste into Figma, Inkscape or a slide. It is offered as `image/svg+xml`, as
plain text (the SVG markup, which is what web apps like Figma read) and as a PNG
for apps that only take pixels. A **Copied** message briefly appears at the
bottom of the page to confirm it.

## Good to know

- In live mode the pad does not store strokes in its memory: folio-board keeps
  them in `~/.local/state/folio-board/drawing.json` (under `$XDG_STATE_HOME`
  if set), saved each time you lift the pen. The settings sit next to it, in
  `settings.json`.
- The pad sleeps after a while without use. If strokes stop appearing, press
  its button, then click **Reconnect**.
- If Tuhi's daemon is installed somewhere other than
  `/usr/libexec/tuhi/tuhi-server`, point to it with
  `TUHI_SERVER=/path/to/tuhi-server folio-board`, or start Tuhi yourself
  before running `folio-board`.

## How it works

Tuhi's `StartLive` D-Bus method expects a file descriptor to `/dev/uhid` and
writes kernel UHID packets to it. folio-board passes one end of a socket pair
instead, decodes the `UHID_INPUT2` packets (in-range flag, x, y, pressure)
itself and renders them with cairo. Because no kernel device is created, the
pen never moves your cursor and `/dev/uhid` permissions don't matter.

## Architecture

The code follows the hexagonal architecture (ports and adapters), as laid out in
[Garrido de Paz's implementation guide](https://jmgarridopaz.github.io/content/hexagonalarchitecture-ig/intro.html).
`folio_board/hexagon` holds what the application does, with no GTK, Tuhi, cairo
or file access. It talks to the outside world only through ports, each named
for what it is used for:

| Side   | Actor     | Port                          | Adapter                          |
| ------ | --------- | ----------------------------- | -------------------------------- |
| Driver | Presenter | `for_presenting_drawings`     | GTK window                       |
| Driver | Pad       | `for_receiving_pen_input`     | Tuhi live mode (D-Bus, UHID)     |
| Driven | Pad       | `for_linking_the_pad`         | Tuhi live mode                   |
| Driven | Presenter | `for_notifying_the_presenter` | GTK window                       |
| Driven | Images    | `for_encoding_images`         | cairo (SVG, PNG)                 |
| Driven | Files     | `for_storing_drawings`        | file system                      |
| Driven | Memory    | `for_remembering_the_drawing` | JSON file                        |
| Driven | Memory    | `for_remembering_settings`    | JSON file                        |
| Driven | Clipboard | `for_sharing_drawings`        | GTK clipboard                    |
| Driven | Clock     | `for_telling_time`            | monotonic clock                  |

Adapters live in `folio_board/adapter/<port>/<technology>`, and
`folio_board/startup.py` wires them to the hexagon.

Ports are plain base classes that their implementations subclass explicitly, so
an editor can navigate them. *Show type hierarchy* (subtypes) on a port lists
the adapters and test doubles behind a driven port, and the hexagon behind a
driver port. *Go to implementation* on a port method does the same. *Find
references* on a driver port finds the driver adapters that call it.
`pyrefly.toml` makes pyrefly index the whole project for this.

### Tests

```sh
sudo pacman -S python-pytest     # or: sudo dnf install python3-pytest / sudo apt install python3-pytest
python -m pytest
```

`tests/hexagon` drives the application through its driver ports, with the test
doubles of `tests/doubles.py` on the driven ones, so it runs without a pad or a
display. `tests/adapter` covers UHID decoding, image encoding, storage, and the
kept drawing and settings, and `tests/test_hexagon_isolation.py` checks that
the hexagon imports nothing from the outside world.

`tests/fixtures/shape_samples.json` holds boxes, arrows, a circle, handwriting
and doodles drawn on a Bamboo Folio. Shape recognition is tested, and its
thresholds were tuned, on these strokes: when a shape you draw is missed, or
something snaps that should not, adding it there makes a test case.

## License

MIT, see [LICENSE](LICENSE).
