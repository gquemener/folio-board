"""Driven port for turning a page into an image file's bytes."""
from typing import Literal

from folio_board.hexagon.driver.for_presenting_drawings import Page

Format = Literal['svg', 'png']


class EncodingError(Exception):
    pass


class ForEncodingImages:
    def encode(self, page: Page, fmt: Format) -> bytes:
        """The page's crop, or the whole page, as SVG (true to paper size) or PNG.
        The hover point is left out. Raises EncodingError."""
        raise NotImplementedError
