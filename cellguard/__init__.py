"""CellGuard: statistical disclosure control for magnitude tables.

A small, readable toolkit that shows how official statistics are protected
before they are published:

* build flexible magnitude tables from business microdata,
* measure disclosure risk with the p% rule and the (n, k) dominance rule,
* protect the tables with the Cell Key Method and with cell suppression,
* measure how much information the protection costs,
* trade risk against utility and draw the confidentiality map.

Nothing here is a production disclosure control system. It is a teaching
model that implements the real ideas in a form you can read end to end.
"""

__version__ = "0.1.0"
