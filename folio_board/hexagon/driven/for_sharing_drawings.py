"""Driven port for handing a drawing to other applications, e.g. through the clipboard."""


class ForSharingDrawings:
    def share(self, svg: bytes, png: bytes) -> None:
        """Offer the same drawing as SVG and as PNG; the receiving app picks one."""
        raise NotImplementedError
