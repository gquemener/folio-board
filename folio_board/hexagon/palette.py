"""The colors of the palette strip: the 16 CGA / EGA colors of 8-bit era PCs."""

# A band 15 mm high, 15 mm below the top edge of the pad, in the default portrait orientation.
STRIP_TOP_MM = 15
STRIP_MM = 15

COLORS = [
    ('Black', 0x000000),
    ('Blue', 0x0000AA),
    ('Green', 0x00AA00),
    ('Cyan', 0x00AAAA),
    ('Red', 0xAA0000),
    ('Magenta', 0xAA00AA),
    ('Brown', 0xAA5500),
    ('Light gray', 0xAAAAAA),
    ('Dark gray', 0x555555),
    ('Light blue', 0x5555FF),
    ('Light green', 0x55FF55),
    ('Light cyan', 0x55FFFF),
    ('Light red', 0xFF5555),
    ('Light magenta', 0xFF55FF),
    ('Yellow', 0xFFFF55),
    ('White', 0xFFFFFF),
]


def rgb(value):
    return tuple(((value >> shift) & 0xFF) / 255 for shift in (16, 8, 0))
