"""The pen colors, picked with the keys & é " ' ( - è _ ç of a French keyboard, in this order."""

COLORS = [
    ('Black', 0x000000),
    ('Orange', 0xF57C00),
    ('Blue', 0x1E5BD6),
    ('Green', 0x2E9D46),
    ('Yellow', 0xF2C200),
    ('Red', 0xD62828),
    ('Lilac', 0x9B6BD3),
    ('Pink', 0xE85A9E),
    ('Brown', 0x8B5A2B),
]


def rgb(value):
    return tuple(((value >> shift) & 0xFF) / 255 for shift in (16, 8, 0))
