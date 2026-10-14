"""The hexagon: what folio-board does, independent of GTK, Tuhi, cairo or the file system.

It talks to the outside world only through the ports in driver/ (what actors use the
application for) and driven/ (what the application uses actors for), and imports nothing
beyond the standard library.

Ports are plain base classes, and whatever implements one subclasses it explicitly, so
"go to implementation" on a port lists the hexagon or the adapters behind it. They are
not typing.Protocol classes: a GTK widget cannot subclass a Protocol (metaclass conflict).
"""
