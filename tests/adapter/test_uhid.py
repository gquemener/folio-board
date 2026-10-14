import struct

from folio_board.adapter.for_receiving_pen_input.tuhi.uhid import (
    UHID_CREATE2, UHID_INPUT2, PadCreated, PenReport, decode)


def create2(rdesc):
    """A UHID_CREATE2 packet: type, then struct uhid_create2_req with rd_size at 260 and rd_data at 280."""
    packet = bytearray(4 + 280 + len(rdesc))
    struct.pack_into('<L', packet, 0, UHID_CREATE2)
    struct.pack_into('<H', packet, 260, len(rdesc))
    packet[280:] = rdesc
    return bytes(packet)


def test_input_is_a_pen_report():
    packet = struct.pack('<LHBBHHH', UHID_INPUT2, 8, 2, 1, 1200, 3400, 512)
    assert decode(packet) == PenReport(True, 1200, 3400, 512)


def test_create_reads_the_pressure_maximum():
    rdesc = bytes([0x05, 0x0d, 0x09, 0x30, 0x27]) + struct.pack('<i', 8191) + bytes([0x81, 0x02])
    assert decode(create2(rdesc)) == PadCreated(8191)


def test_create_without_pressure_usage_has_no_maximum():
    assert decode(create2(bytes([0x05, 0x0d, 0x09, 0x42]))) == PadCreated(None)


def test_truncated_create_has_no_maximum():
    assert decode(struct.pack('<L', UHID_CREATE2) + bytes(100)) == PadCreated(None)


def test_other_packets_are_ignored():
    assert decode(struct.pack('<L', 99) + bytes(20)) is None
