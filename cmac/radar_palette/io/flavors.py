"""Detection of, and conversion between, radar/grid object flavours.

The functions here are the single place this package decides "which object family
is this, and which should I hand back". Keeping that in one module means an
operator's own code stays free of isinstance ladders, and the conversion sharp
edges are documented and tested in one place rather than rediscovered per call
site.

Conversion strategy
-------------------
Py-ART owns the mapping between its data model and xradar's, so conversions
delegate to it:

- ``DataTree`` to a Py-ART surface: ``DataTree.pyart.to_radar()``, which returns a
  :class:`pyart.xradar.Xradar` wrapper presenting the ``Radar`` API over the live
  tree. Py-ART operators accept it directly.
- ``Radar`` to ``DataTree``: written as cfradial1 and reopened with
  :func:`xradar.io.open_cfradial1_datatree`. This goes through a temporary file
  because Py-ART exposes no in-memory equivalent; the file format is the
  interchange contract, so the round trip is exactly what a user would get by
  writing and reloading.
- ``Grid`` to ``Dataset``: :meth:`pyart.core.Grid.to_xarray`.
- ``Dataset`` to a Py-ART grid surface: :class:`pyart.xradar.Xgrid`.

Sharp edges these functions absorb
----------------------------------
``Xgrid`` rejects a dataset whose ``time`` has been decoded to datetimes, but
``Grid.to_xarray`` produces exactly that --- so the dataset is re-encoded to CF
offsets before wrapping.

Assigning ``Xradar.time`` mutates only the wrapper: the change does not reach the
underlying ``DataTree``, so a caller who updates times through the Py-ART surface
and then reads the tree silently sees the old clock. Time is therefore written
back explicitly, per sweep, by :func:`write_ray_times_to_datatree`. (Field
assignment via ``add_field`` *does* write through --- the asymmetry is why this is
easy to get wrong.)
"""

from __future__ import annotations

import tempfile
from enum import Enum
from pathlib import Path

import numpy as np

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


class RadarFlavor(Enum):
    """Object family of a radar volume.

    Attributes
    ----------
    PYART
        :class:`pyart.core.Radar`.
    XRADAR
        :class:`xarray.DataTree` following the xradar/CfRadial2 layout, or the
        :class:`pyart.xradar.Xradar` wrapper around one.
    """

    PYART = "pyart"
    XRADAR = "xradar"


class GridFlavor(Enum):
    """Object family of a Cartesian grid.

    Attributes
    ----------
    PYART
        :class:`pyart.core.Grid`.
    XARRAY
        :class:`xarray.Dataset`.
    """

    PYART = "pyart"
    XARRAY = "xarray"


_GRID_FLAVOR_ALIASES = {"xradar": GridFlavor.XARRAY}


def _import_pyart():
    """Import Py-ART, raising a clear error if it is unavailable."""
    try:
        import pyart
    except ImportError as error:  # pragma: no cover - pyart is a core dependency
        raise ImportError(
            "Py-ART is required for radar/grid conversions; install arm_pyart"
        ) from error
    return pyart


def _import_xradar():
    """Import xradar and xarray, raising a clear error if either is unavailable."""
    try:
        import xarray
        import xradar
    except ImportError as error:  # pragma: no cover - both are core dependencies
        raise ImportError(
            "xradar and xarray are required for DataTree conversions"
        ) from error
    return xradar, xarray


def detect_radar_flavor(radar_like):
    """Identify which object family a radar volume belongs to.

    Parameters
    ----------
    radar_like : object
        A :class:`pyart.core.Radar`, an :class:`xarray.DataTree`, or a
        :class:`pyart.xradar.Xradar` wrapper.

    Returns
    -------
    RadarFlavor
        The family ``radar_like`` belongs to. An ``Xradar`` wrapper reports
        ``XRADAR``: it presents a Py-ART surface, but its home representation is
        the tree it wraps, and that is what a caller passing one expects back.

    Raises
    ------
    TypeError
        If the object is not a recognised radar volume.
    """
    pyart = _import_pyart()
    _, xarray = _import_xradar()

    if isinstance(radar_like, pyart.xradar.Xradar):
        return RadarFlavor.XRADAR
    if isinstance(radar_like, xarray.DataTree):
        return RadarFlavor.XRADAR
    if isinstance(radar_like, pyart.core.Radar):
        return RadarFlavor.PYART
    raise TypeError(
        "expected a Py-ART Radar, an xradar DataTree, or a pyart.xradar.Xradar "
        f"wrapper, got {type(radar_like).__name__}"
    )


def detect_grid_flavor(grid_like):
    """Identify which object family a Cartesian grid belongs to.

    Parameters
    ----------
    grid_like : object
        A :class:`pyart.core.Grid`, an :class:`xarray.Dataset`, or a
        :class:`pyart.xradar.Xgrid` wrapper.

    Returns
    -------
    GridFlavor
        The family ``grid_like`` belongs to.

    Raises
    ------
    TypeError
        If the object is not a recognised Cartesian grid.
    """
    pyart = _import_pyart()
    _, xarray = _import_xradar()

    if isinstance(grid_like, xarray.Dataset):
        return GridFlavor.XARRAY
    if isinstance(grid_like, pyart.core.Grid | pyart.xradar.Xgrid):
        return GridFlavor.PYART
    raise TypeError(
        f"expected a Py-ART Grid or an xarray Dataset, got {type(grid_like).__name__}"
    )


def resolve_output_flavor(requested, input_flavor):
    """Decide the output flavour from an optional request and the input flavour.

    Parameters
    ----------
    requested : RadarFlavor or GridFlavor or str or None
        Explicitly requested output flavour. ``None`` mirrors the input, which is
        the default behaviour of every entry point in this package. Strings are
        matched case-insensitively; ``"xradar"`` is accepted as an alias for
        ``GridFlavor.XARRAY`` when resolving a grid flavour, since a caller
        working in xradar naturally names the whole ecosystem.
    input_flavor : RadarFlavor or GridFlavor
        Flavour of the object the caller supplied. Determines which enumeration
        the result is drawn from.

    Returns
    -------
    RadarFlavor or GridFlavor
        The flavour to return to the caller, in the same family as
        ``input_flavor``.

    Raises
    ------
    ValueError
        If ``requested`` names an unknown flavour, or belongs to a different
        family than ``input_flavor`` (asking for a grid flavour on a radar
        conversion is a programming error, not a coercion to perform).
    """
    flavor_family = type(input_flavor)
    if requested is None:
        return input_flavor
    if isinstance(requested, flavor_family):
        return requested
    if isinstance(requested, RadarFlavor | GridFlavor):
        raise ValueError(
            f"expected a {flavor_family.__name__}, got {type(requested).__name__}"
        )

    normalised = str(requested).strip().lower()
    if flavor_family is GridFlavor and normalised in _GRID_FLAVOR_ALIASES:
        return _GRID_FLAVOR_ALIASES[normalised]
    for candidate in flavor_family:
        if candidate.value == normalised:
            return candidate
    valid = ", ".join(sorted(member.value for member in flavor_family))
    raise ValueError(f"unknown output flavour {requested!r}; expected one of {valid}")


def to_pyart_radar(radar_like):
    """Present any supported radar volume as a Py-ART ``Radar`` surface.

    Parameters
    ----------
    radar_like : pyart.core.Radar or xarray.DataTree or pyart.xradar.Xradar
        Volume to adapt. Not copied: the returned object reads through to the
        caller's data.

    Returns
    -------
    radar : pyart.core.Radar or pyart.xradar.Xradar
        An object exposing the Py-ART ``Radar`` API. For xradar input this is an
        ``Xradar`` wrapper over the live tree, which Py-ART operators accept
        directly.
    input_flavor : RadarFlavor
        Flavour of the supplied object, for use with
        :func:`resolve_output_flavor`.

    Notes
    -----
    Updating times through the returned wrapper does **not** propagate to the
    underlying ``DataTree``; use :func:`write_ray_times_to_datatree` for that.
    """
    input_flavor = detect_radar_flavor(radar_like)
    pyart = _import_pyart()

    if isinstance(radar_like, pyart.xradar.Xradar) or isinstance(
        radar_like, pyart.core.Radar
    ):
        return radar_like, input_flavor
    return radar_like.pyart.to_radar(), input_flavor


def _pyart_radar_to_datatree(radar):
    """Convert a Py-ART ``Radar`` to an xradar ``DataTree`` via cfradial1.

    Py-ART exposes no in-memory ``Radar`` to ``DataTree`` conversion, so this
    round-trips through a temporary cfradial1 file --- the same interchange path a
    user gets by writing and reloading, which keeps the conversion honest about
    what survives the format.
    """
    pyart = _import_pyart()
    xradar, _ = _import_xradar()

    with tempfile.TemporaryDirectory(dir=Path.cwd()) as staging_directory:
        cfradial_path = str(Path(staging_directory) / "volume.nc")
        pyart.io.write_cfradial(cfradial_path, radar)
        datatree = xradar.io.open_cfradial1_datatree(cfradial_path)
        return datatree.load()


def to_radar_flavor(radar, output_flavor):
    """Return a radar volume in the requested object family.

    Parameters
    ----------
    radar : pyart.core.Radar or pyart.xradar.Xradar or xarray.DataTree
        Volume to convert.
    output_flavor : RadarFlavor or str
        Family to return. Strings are matched case-insensitively.

    Returns
    -------
    pyart.core.Radar or xarray.DataTree
        The volume in the requested family.

    Raises
    ------
    ValueError
        If ``output_flavor`` names an unknown flavour.
    """
    pyart = _import_pyart()
    output_flavor = resolve_output_flavor(output_flavor, detect_radar_flavor(radar))

    if output_flavor is RadarFlavor.XRADAR:
        if isinstance(radar, pyart.xradar.Xradar):
            return radar.xradar
        _, xarray = _import_xradar()
        if isinstance(radar, xarray.DataTree):
            return radar
        return _pyart_radar_to_datatree(radar)

    if isinstance(radar, pyart.core.Radar):
        return radar
    return _datatree_to_pyart_radar(radar)


def _datatree_to_pyart_radar(radar_like):
    """Convert xradar input to a true :class:`pyart.core.Radar` via cfradial1.

    ``DataTree.pyart.to_radar()`` yields an ``Xradar`` wrapper rather than a
    ``Radar``. A caller who explicitly asks for the Py-ART flavour wants the real
    class, so this writes cfradial2-compatible output and reads it back with
    Py-ART.
    """
    pyart = _import_pyart()
    xradar, xarray = _import_xradar()

    # Unwrap an Xradar wrapper to the tree it holds. The isinstance check is
    # deliberate: xradar registers an accessor named ``xradar`` on DataTree, so a
    # hasattr("xradar") probe is true for a bare tree as well and would hand back
    # the accessor instead of the data.
    if isinstance(radar_like, pyart.xradar.Xradar):
        datatree = radar_like.xradar
    elif isinstance(radar_like, xarray.DataTree):
        datatree = radar_like
    else:  # pragma: no cover - guarded by detect_radar_flavor
        raise TypeError(f"cannot convert {type(radar_like).__name__} to a Radar")

    with tempfile.TemporaryDirectory(dir=Path.cwd()) as staging_directory:
        cfradial_path = str(Path(staging_directory) / "volume.nc")
        xradar.io.to_cfradial1(datatree.copy(), cfradial_path)
        return pyart.io.read_cfradial(cfradial_path)


def write_ray_times_to_datatree(datatree, time_dict):
    """Write per-ray times into a ``DataTree``, distributing them across sweeps.

    Assigning ``Xradar.time`` updates only the wrapper --- the underlying tree keeps
    its original clock, so a caller who sets times through the Py-ART surface and
    then reads the tree silently gets stale values. This writes them back for real.

    Parameters
    ----------
    datatree : xarray.DataTree
        Tree to update, in place. One group per sweep.
    time_dict : dict
        Py-ART style time dictionary: ``data`` holds per-ray offsets for the whole
        volume, concatenated in sweep order, and ``units`` the CF reference-time
        string. Offsets are decoded and stored as datetime64, matching how xradar
        represents sweep time.

    Returns
    -------
    xarray.DataTree
        ``datatree``, to allow use as an expression.

    Raises
    ------
    ValueError
        If the number of offsets does not match the tree's total ray count.
    """
    _, xarray = _import_xradar()
    from netCDF4 import num2date

    sweep_group_names = sorted(
        (name for name in datatree.groups if name.startswith("/sweep_")),
        key=lambda name: int(name.rsplit("_", 1)[1]),
    )
    rays_per_sweep = [
        datatree[name].ds.sizes[datatree[name].ds["time"].dims[0]]
        for name in sweep_group_names
    ]
    total_rays = sum(rays_per_sweep)

    offsets = np.asarray(time_dict["data"], dtype="float64").ravel()
    if offsets.size != total_rays:
        raise ValueError(
            f"got {offsets.size} ray times for a volume with {total_rays} rays"
        )

    absolute_times = np.asarray(
        num2date(
            offsets,
            time_dict["units"],
            calendar=time_dict.get("calendar", "gregorian"),
            only_use_cftime_datetimes=False,
            only_use_python_datetimes=True,
        ),
        dtype="datetime64[ns]",
    )

    first_ray_index = 0
    for group_name, ray_count in zip(sweep_group_names, rays_per_sweep, strict=True):
        sweep_dataset = datatree[group_name].ds
        time_dimension = sweep_dataset["time"].dims[0]
        sweep_times = absolute_times[first_ray_index : first_ray_index + ray_count]
        datatree[group_name].ds = sweep_dataset.assign_coords(
            time=xarray.DataArray(
                sweep_times,
                dims=(time_dimension,),
                attrs=dict(sweep_dataset["time"].attrs),
            )
        )
        first_ray_index += ray_count

    return datatree


def to_pyart_grid(grid_like):
    """Present any supported Cartesian grid as a Py-ART ``Grid`` surface.

    Parameters
    ----------
    grid_like : pyart.core.Grid or xarray.Dataset
        Grid to adapt.

    Returns
    -------
    pyart.core.Grid or pyart.xradar.Xgrid
        An object exposing the Py-ART ``Grid`` API.

    Notes
    -----
    :class:`pyart.xradar.Xgrid` requires ``time`` to be *undecoded* (CF offsets
    with a ``units`` attribute), while :meth:`pyart.core.Grid.to_xarray` produces
    decoded datetimes. This re-encodes before wrapping, so datasets from either
    origin work.
    """
    pyart = _import_pyart()
    if detect_grid_flavor(grid_like) is GridFlavor.PYART:
        return grid_like
    return pyart.xradar.Xgrid(_encode_dataset_time(grid_like))


def _encode_dataset_time(dataset):
    """Return ``dataset`` with ``time`` as CF offsets carrying a ``units`` attribute.

    ``Xgrid`` detects decoded times by the absence of ``units`` and refuses to
    wrap such a dataset. Datasets already carrying ``units`` are returned
    untouched.
    """
    if "units" in dataset["time"].attrs:
        return dataset

    _, xarray = _import_xradar()
    time_values = np.atleast_1d(dataset["time"].values)
    epoch = np.datetime64(time_values[0], "s")
    offsets = (
        time_values.astype("datetime64[ns]") - epoch.astype("datetime64[ns]")
    ) / np.timedelta64(1, "s")
    units = f"seconds since {str(epoch).replace('T', ' ')}"

    encoded = dataset.assign_coords(
        time=xarray.DataArray(
            np.asarray(offsets, dtype="float64"),
            dims=dataset["time"].dims,
            attrs={**dataset["time"].attrs, "units": units},
        )
    )
    return encoded


def to_grid_flavor(grid, output_flavor):
    """Return a Cartesian grid in the requested object family.

    Parameters
    ----------
    grid : pyart.core.Grid or xarray.Dataset
        Grid to convert.
    output_flavor : GridFlavor or str
        Family to return. ``"xradar"`` is accepted as an alias for ``"xarray"``.

    Returns
    -------
    pyart.core.Grid or xarray.Dataset
        The grid in the requested family.

    Raises
    ------
    ValueError
        If ``output_flavor`` names an unknown flavour.
    """
    _, xarray = _import_xradar()
    output_flavor = resolve_output_flavor(output_flavor, detect_grid_flavor(grid))

    if output_flavor is GridFlavor.XARRAY:
        if isinstance(grid, xarray.Dataset):
            return grid
        return grid.to_xarray()

    if isinstance(grid, xarray.Dataset):
        return to_pyart_grid(grid)
    return grid
