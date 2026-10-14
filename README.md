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
install -Dm755 folio-board/folio-board ~/.local/bin/folio-board
```

Make sure `~/.local/bin` is in your `PATH`.

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

| Action             | Button    | Key        |
| ------------------ | --------- | ---------- |
| Clear the page     | Clear     | `c`        |
| Undo last stroke   | Undo      | `Ctrl+Z`   |
| Rotate the page    | Rotate    | `r`        |
| Pressure on/off    | Pressure  | `p`        |
| Save as PNG or SVG | Save      | `Ctrl+S`   |
| Force a reconnect  | Reconnect |            |
| Quit               |           | `q`, `Esc` |

With **Pressure** checked (the default), pressing harder draws a thicker line.
Uncheck it to draw every stroke at the same width.

The red dot shows where the pen hovers, so viewers can follow it before it
touches the paper.

Save opens a file dialog in your Pictures folder. The format follows the file
extension: `.svg` gives a vector file at the paper's real size, anything else a
200 DPI PNG. The saved page uses the board's current rotation and leaves out the
hover dot.

## Good to know

- In live mode the pad does not store strokes in its memory: what you draw
  only exists in the window.
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

## License

MIT, see [LICENSE](LICENSE).
