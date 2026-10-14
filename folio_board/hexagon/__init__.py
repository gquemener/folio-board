"""The hexagon: what folio-board does, independent of GTK, Tuhi, cairo or the file system.

It talks to the outside world only through the ports in driver/ (what actors use the
application for) and driven/ (what the application uses actors for), and imports nothing
beyond the standard library.
"""
