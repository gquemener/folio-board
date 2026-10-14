"""The pad through Tuhi's live mode, over D-Bus.

Tuhi's live mode expects a /dev/uhid fd and writes kernel UHID packets to it. We hand it
one end of a socketpair instead, so no system tablet is created (the cursor stays put) and
no root access is needed: we decode the UHID packets ourselves.

TuhiPad plays both sides of the pad actor: it implements the driven port
ForLinkingThePad (start and stop live mode) and drives ForReceivingPenInput with what
the pad sends.
"""
import os
import socket
import subprocess
import time

import gi

gi.require_version('GLibUnix', '2.0')
from gi.repository import Gio, GLib, GLibUnix  # noqa: E402

from folio_board.adapter.for_receiving_pen_input.tuhi import uhid  # noqa: E402
from folio_board.hexagon.driven.for_linking_the_pad import PadLinkError  # noqa: E402

BUS = 'org.freedesktop.tuhi1'
DEVICE_IFACE = 'org.freedesktop.tuhi1.Device'
MANAGER_PATH = '/org/freedesktop/tuhi1'
TUHI_SERVER = os.environ.get('TUHI_SERVER', '/usr/libexec/tuhi/tuhi-server')
CHECK_SECONDS = 2


class TuhiError(Exception):
    """Tuhi cannot be used; the message says what to do."""


class TuhiPad:
    def __init__(self, address=None):
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION)
        self.server = ensure_tuhi(self.bus)
        try:
            self.device_path = find_device(self.bus, address)
            drop_stale_connection(self.bus, self.device_path)
        except Exception:
            self.close()
            raise
        self.pen_input = None
        self.sock = None
        self.watch = None

    def dimensions_um(self):
        """The pad's drawing area as tuhi knows it, (0, 0) if it has not read it yet."""
        return tuple(self._get_property('Dimensions'))

    def drive(self, pen_input):
        """Start reporting to pen_input, a ForReceivingPenInput."""
        self.pen_input = pen_input
        self.bus.signal_subscribe(BUS, None, None, self.device_path, None,
                                  Gio.DBusSignalFlags.NONE, self._on_signal)
        GLib.timeout_add_seconds(CHECK_SECONDS, self._on_check)

    def close(self):
        """Stop the tuhi-server we started, if any."""
        if self.server:
            self.server.terminate()
            self.server = None

    # ForLinkingThePad

    def start_live(self):
        ours, theirs = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.sock = ours
        self.watch = GLibUnix.fd_add_full(GLib.PRIORITY_DEFAULT, ours.fileno(),
                                          GLib.IOCondition.IN, self._on_packet)
        fds = Gio.UnixFDList.new()
        fds.append(theirs.fileno())
        result, _ = self.bus.call_with_unix_fd_list_sync(
            BUS, self.device_path, DEVICE_IFACE, 'StartLive',
            GLib.Variant('(h)', (0,)), GLib.VariantType('(i)'),
            Gio.DBusCallFlags.NONE, -1, fds, None)
        theirs.close()
        if result[0] != 0:
            raise PadLinkError(result[0])

    def stop_live(self):
        # StopLive is declared NoReply, so a sync call would block until timeout.
        self.bus.call(BUS, self.device_path, DEVICE_IFACE, 'StopLive', None, None,
                      Gio.DBusCallFlags.NONE, -1, None, None, None)
        if self.watch:
            GLib.source_remove(self.watch)
            self.watch = None
        if self.sock:
            self.sock.close()
            self.sock = None

    # Driving ForReceivingPenInput

    def _on_packet(self, _fd, _cond):
        packet = self.sock.recv(8192)
        if not packet:
            return GLib.SOURCE_REMOVE
        event = uhid.decode(packet)
        if isinstance(event, uhid.PadCreated):
            self.pen_input.pad_connected(event.pressure_max)
        elif isinstance(event, uhid.PenReport):
            self.pen_input.pen(event.in_range, event.x, event.y, event.pressure)
        return GLib.SOURCE_CONTINUE

    def _on_signal(self, _conn, _sender, _obj, _iface, name, params):
        if name == 'PropertiesChanged':
            w_um, h_um = params[1].get('Dimensions', (0, 0))
            self.pen_input.pad_resized(w_um, h_um)
        elif name == 'LiveStopped':
            self.pen_input.pad_lost(params[0])

    def _on_check(self):
        self.pen_input.check_connection()
        return GLib.SOURCE_CONTINUE

    def _get_property(self, name):
        return self.bus.call_sync(BUS, self.device_path, 'org.freedesktop.DBus.Properties', 'Get',
                                  GLib.Variant('(ss)', (DEVICE_IFACE, name)),
                                  GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, -1, None).unpack()[0]


def tuhi_running(bus):
    owner = bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
                          'NameHasOwner', GLib.Variant('(s)', (BUS,)), GLib.VariantType('(b)'),
                          Gio.DBusCallFlags.NONE, -1, None)
    return owner.unpack()[0]


def ensure_tuhi(bus):
    """Start tuhi-server if nobody provides it; return the process we started, if any."""
    if tuhi_running(bus):
        return None
    try:
        server = subprocess.Popen([TUHI_SERVER])
    except FileNotFoundError:
        raise TuhiError(f'tuhi is not running and {TUHI_SERVER} was not found. '
                        'Start Tuhi yourself or set TUHI_SERVER to its path.') from None
    for _ in range(50):
        if tuhi_running(bus):
            return server
        time.sleep(0.2)
    server.terminate()
    raise TuhiError('tuhi-server did not show up on the session bus')


def find_device(bus, address):
    if address:
        return MANAGER_PATH + '/' + address.replace(':', '_')
    devices = bus.call_sync(BUS, MANAGER_PATH, 'org.freedesktop.DBus.Properties', 'Get',
                            GLib.Variant('(ss)', ('org.freedesktop.tuhi1.Manager', 'Devices')),
                            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
    if not devices:
        raise TuhiError('No registered device: pair your pad once with the Tuhi app first.')
    return devices[0]


def drop_stale_connection(bus, device_path):
    """A pad still connected from a previous tuhi run never switches to live mode."""
    bluez_path = bus.call_sync(BUS, device_path, 'org.freedesktop.DBus.Properties', 'Get',
                               GLib.Variant('(ss)', (DEVICE_IFACE, 'BlueZDevice')),
                               GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
    system_bus = Gio.bus_get_sync(Gio.BusType.SYSTEM)
    try:
        system_bus.call_sync('org.bluez', bluez_path, 'org.bluez.Device1', 'Disconnect',
                             None, None, Gio.DBusCallFlags.NONE, 5000, None)
    except GLib.Error:
        pass
