"""Object-flavour interoperability for radar and grid data.

Two object families describe the same radar data, and users arrive with either:

*Py-ART* --- :class:`pyart.core.Radar` for volumes, :class:`pyart.core.Grid` for
Cartesian output.

*xradar / xarray* --- :class:`xarray.DataTree` for volumes (one group per sweep),
:class:`xarray.Dataset` for Cartesian output.

Operators in this package compute on the Py-ART surface, because that is what the
underlying geometry helpers expect. Rather than requiring callers to convert, the
entry points accept either family and return the family the caller expects. The
default is to *mirror the input*: a ``DataTree`` in gives a ``DataTree`` back, a
``Radar`` in gives a ``Radar`` back, and nobody is silently handed an object of a
different type than they passed.

Conversions delegate to Py-ART's own interoperability layer
(:mod:`pyart.xradar`, :meth:`pyart.core.Grid.to_xarray`, and xradar's cfradial
readers) rather than reimplementing the mapping between the two data models. That
layer is maintained alongside the formats and handles metadata this package has
no business duplicating.
"""

from .flavors import (
    GridFlavor,
    RadarFlavor,
    detect_grid_flavor,
    detect_radar_flavor,
    resolve_output_flavor,
    to_grid_flavor,
    to_pyart_grid,
    to_pyart_radar,
    to_radar_flavor,
    write_ray_times_to_datatree,
)

__all__ = [
    "GridFlavor",
    "RadarFlavor",
    "detect_grid_flavor",
    "detect_radar_flavor",
    "resolve_output_flavor",
    "to_grid_flavor",
    "to_pyart_grid",
    "to_pyart_radar",
    "to_radar_flavor",
    "write_ray_times_to_datatree",
]
