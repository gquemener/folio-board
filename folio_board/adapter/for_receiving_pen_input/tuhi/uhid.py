"""Decode the kernel UHID packets tuhi writes in live mode."""
import struct
from dataclasses import dataclass
from typing import Optional

UHID_CREATE2 = 11
UHID_INPUT2 = 12


@dataclass(frozen=True)
class PadCreated:
    """Tuhi created the tablet device: the pad is live."""
    pressure_max: Optional[int]


@dataclass(frozen=True)
class PenReport:
    in_range: bool
    x: int
    y: int
    pressure: int


def decode(packet):
    """A PadCreated, a PenReport, or None for packets folio-board does not use."""
    kind = struct.unpack_from('<L', packet)[0]
    if kind == UHID_CREATE2:
        try:
            return PadCreated(rdesc_pressure_max(packet))
        except struct.error:
            return PadCreated(None)
    if kind == UHID_INPUT2:
        _report_id, in_range, x, y, pressure = struct.unpack_from('<BBHHH', packet, 6)
        return PenReport(bool(in_range), x, y, pressure)
    return None


def rdesc_pressure_max(packet):
    """Read the Tip Pressure logical maximum from a UHID_CREATE2 packet."""
    # struct uhid_create2_req: name[128] phys[64] uniq[64] rd_size bus vendor product version country rd_data
    rd_size = struct.unpack_from('<H', packet, 260)[0]
    rdesc = packet[280:280 + rd_size]
    # Usage (Tip Pressure) followed by a 4-byte Logical Maximum, as tuhi writes it.
    i = rdesc.find(bytes([0x09, 0x30, 0x27]))
    if i < 0 or i + 7 > len(rdesc):
        return None
    return struct.unpack_from('<i', rdesc, i + 3)[0] or None
