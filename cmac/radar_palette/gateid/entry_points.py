"""Public entry points: classify a radar volume of either object family.

Following the package convention, these accept a Py-ART :class:`~pyart.core.Radar`
or an xradar :class:`~xarray.DataTree` and return the family the caller passed
in, unless ``output_flavor`` asks otherwise. Conversion is delegated to
:mod:`radar_palette.io.flavors`; nothing here reimplements the mapping between
the two data models.

Computation happens on the Py-ART surface, as elsewhere in this package, because
that is where the gate-geometry helpers live.
"""

from __future__ import annotations

import numpy as np

from ..gateid import single
from .features import build_features, resolve_fields
from .multitrip import volume_echo_top
from ..io.flavors import (
    detect_radar_flavor,
    resolve_output_flavor,
    to_pyart_radar,
    to_radar_flavor,
)

__all__ = [
    "gate_id",
    "meteorological_gatefilter",
]

#: Added to the volume echo top to get the second-trip ceiling, so a storm
#: slightly taller than the one sampled is not vetoed.
TRIP_CEILING_MARGIN_M = 3000.0

#: Scan modes whose sweeps are a constant-elevation surface.
PPI_MODES = ("ppi", "sector", "azimuth_surveillance")
#: Scan modes whose sweeps are a vertical cross-section.
RHI_MODES = ("rhi", "elevation_surveillance", "manual_rhi")


def _decode_sweep_modes(radar):
    """Return the decoded ``sweep_mode`` string for each sweep.

    The two object families store this differently and both are easy to get
    wrong. Py-ART holds a masked array of single *characters*, one row per
    sweep, so joining a row without dropping the mask turns ``sector`` into
    byte junk. The :class:`pyart.xradar.Xradar` wrapper instead holds one
    whole byte string per sweep, so splitting it per character yields empty
    strings and every sweep looks like an unknown scan type.

    Both shapes are handled here, and the result is verified by a test that
    runs the same volume through both families.
    """
    raw = np.atleast_1d(radar.sweep_mode["data"])

    def _clean(value):
        if isinstance(value, (bytes, np.bytes_)):
            value = value.decode(errors="replace")
        return str(value).replace("\x00", "").strip().lower()

    # One whole string per sweep (the xradar wrapper).
    if raw.ndim == 1 and raw.dtype.kind in "SU" and raw.dtype.itemsize > 1:
        return [_clean(v) for v in raw]
    if raw.ndim == 1 and raw.dtype.kind == "O":
        return [_clean(v) for v in raw]

    # A row of characters per sweep (Py-ART's CfRadial1 reader).
    modes = []
    for row in np.atleast_2d(raw):
        filled = np.ma.filled(np.ma.asarray(row), b" ").ravel()
        modes.append(
            _clean(
                b"".join(
                    c if isinstance(c, (bytes, np.bytes_)) else str(c).encode()
                    for c in filled
                )
            )
        )
    return modes


def _sweep_geometry_ok(radar, sweep, max_ppi_span=5.0, min_rhi_span=20.0):
    """Whether a sweep is a usable PPI or RHI.

    ``sweep_mode`` is checked *and* the elevation span is measured, because the
    label is not always right: an RHI mislabelled as a PPI, processed as one,
    mixes every elevation into a single surface and yields gate altitudes above
    100 km.
    """
    modes = _decode_sweep_modes(radar)
    mode = modes[sweep] if sweep < len(modes) else ""
    elev = radar.elevation["data"][radar.get_slice(sweep)]
    elev = np.asarray(elev, dtype="f8")
    elev = elev[np.isfinite(elev)]
    if elev.size == 0:
        return False, mode, np.nan
    span = float(elev.max() - elev.min())
    if mode.startswith(PPI_MODES):
        return span <= max_ppi_span, mode, span
    if mode.startswith(RHI_MODES):
        return span >= min_rhi_span, mode, span
    return False, mode, span


def _nyquist_velocity(radar, radar_like=None):
    """Nyquist velocity in m/s, or NaN.

    Py-ART keeps this in ``instrument_parameters``; the xradar layout keeps a
    ``nyquist_velocity`` variable on each sweep and the Py-ART wrapper does not
    surface it, so the tree is consulted directly as a fallback. Losing it is
    not harmless: without a Nyquist the folding-aware velocity texture cannot
    be computed, and the phase-coherence test that identifies second trip and
    receiver noise silently disappears.
    """
    params = getattr(radar, "instrument_parameters", None) or {}
    if "nyquist_velocity" in params:
        vals = np.asarray(params["nyquist_velocity"]["data"], dtype="f8")
        vals = vals[np.isfinite(vals)]
        if vals.size:
            return float(np.median(vals))

    tree = getattr(radar, "ds", None) or radar_like
    children = getattr(tree, "children", None)
    if children:
        found = []
        for key in children:
            if not str(key).startswith("sweep"):
                continue
            node = tree[key]
            data = node.to_dataset() if hasattr(node, "to_dataset") else node
            if "nyquist_velocity" in data:
                vals = np.asarray(data["nyquist_velocity"].values, dtype="f8")
                vals = vals[np.isfinite(vals)]
                if vals.size:
                    found.append(float(np.median(vals)))
        if found:
            return float(np.median(found))
    return np.nan


def gate_id(
    radar_like,
    freezing_level_m=None,
    temperature_field=None,
    field_name="gate_id",
    texture_window=4,
    add_margin=True,
    snr_min=3.0,
    vel_texture_max=None,
    min_run=3,
    despeckle_keep_dbz=30.0,
    incoherent_frac=single.INCOHERENT_TEXTURE_FRAC,
    output_flavor=None,
    replace_existing=True,
):
    """Classify the dominant scatterer at every gate.

    Parameters
    ----------
    radar_like : pyart.core.Radar or xarray.DataTree
        Volume carrying uncorrected polarimetric moments.
    freezing_level_m : float, optional
        Height of the 0 degC level, metres MSL. Enables the melting-layer hard
        constraints and, absent ``temperature_field``, a lapse-rate temperature.
    temperature_field : str, optional
        Name of a field holding gate temperature in degrees Celsius. Strongly
        preferred over the lapse-rate fallback; the choice is recorded in the
        returned metadata as ``temp_source``.
    field_name : str, optional
        Output field name.
    texture_window : int, optional
        Footprint of the texture operator, in gates and rays.
    add_margin : bool, optional
        Also write ``<field_name>_margin``, the winning minus runner-up score.
    snr_min : float or None, optional
        Gates below this SNR are forced to ``no_scatter`` before scoring.
    vel_texture_max : float or None, optional
        Absolute velocity-texture cut in m/s. Normally leave this ``None`` and
        use ``incoherent_frac``, which is independent of PRF.
    min_run : int, optional
        Class runs shorter than this many gates along a ray are dissolved.
    despeckle_keep_dbz : float or None, optional
        Reflectivity at or above which a gate is never despeckled or gated out.
    incoherent_frac : float or None, optional
        Velocity texture, as a fraction of the uniform-random-phase limit,
        above which a gate cannot be first-trip weather.
    output_flavor : RadarFlavor or str or None, optional
        Family to return. Defaults to mirroring the input.
    replace_existing : bool, optional
        Overwrite an existing field of the same name.

    Returns
    -------
    radar : pyart.core.Radar or xarray.DataTree
        The input volume with ``gate_id`` attached, in the requested family.
    meta : dict
        Resolved field names, missing fields, temperature provenance, per-class
        gate counts, and the number of gates removed by each speckle control.

    Notes
    -----
    Sweeps whose geometry is unusable are left unclassified and reported in
    ``meta['skipped_sweeps']`` rather than silently producing wrong answers.

    Examples
    --------
    Classify a Py-ART volume::

        radar, meta = gate_id(radar, freezing_level_m=4670.0)

    Classify an xradar volume and get a ``DataTree`` back::

        tree, meta = gate_id(tree, freezing_level_m=4670.0)
    """
    input_flavor = detect_radar_flavor(radar_like)
    output_flavor = resolve_output_flavor(output_flavor, input_flavor)
    radar, _ = to_pyart_radar(radar_like)

    resolved, missing = resolve_fields(radar.fields)
    if "z" not in resolved or "rhohv" not in resolved:
        raise ValueError(
            f"gate_id needs at least reflectivity and RhoHV; missing {sorted(missing)}"
        )

    shape = (radar.nrays, radar.ngates)
    codes = np.zeros(shape, dtype="i2")
    margin = np.full(shape, np.nan, dtype="f8")
    counts = dict.fromkeys(single.CLASSES.values(), 0)
    skipped, n_noise, n_speck = [], 0, 0

    nyquist = _nyquist_velocity(radar, radar_like)
    params = getattr(radar, "instrument_parameters", None) or {}

    # The second-trip ceiling is a property of the storm, so it is derived
    # once over every usable sweep rather than per sweep. See
    # radar_palette.gateid.multitrip.volume_echo_top for why this matters.
    trip_ceiling_m, ceiling_source = None, "sweep_echo_top"
    if radar.nsweeps > 1:
        pairs = []
        for sweep in range(radar.nsweeps):
            ok, _, _ = _sweep_geometry_ok(radar, sweep)
            if not ok:
                continue
            sl = radar.get_slice(sweep)
            pairs.append(
                (
                    np.ma.filled(
                        radar.fields[resolved["z"]]["data"][sl].astype("f8"), np.nan
                    ),
                    np.asarray(radar.gate_altitude["data"][sl], dtype="f8"),
                )
            )
        top = volume_echo_top(pairs) if pairs else np.nan
        if np.isfinite(top):
            trip_ceiling_m = float(top) + TRIP_CEILING_MARGIN_M
            ceiling_source = "volume_echo_top"

    temp_source = "none"
    for sweep in range(radar.nsweeps):
        ok, mode, span = _sweep_geometry_ok(radar, sweep)
        if not ok:
            skipped.append({"sweep": sweep, "sweep_mode": mode, "elevation_span": span})
            continue
        sl = radar.get_slice(sweep)
        moments = {
            key: np.ma.filled(radar.fields[name]["data"][sl].astype("f8"), np.nan)
            for key, name in resolved.items()
        }
        temperature = None
        if temperature_field and temperature_field in radar.fields:
            temperature = np.ma.filled(
                radar.fields[temperature_field]["data"][sl].astype("f8"), np.nan
            )

        prt = None
        if "prt" in params:
            values = np.asarray(params["prt"]["data"], dtype="f8")[sl]
            values = values[np.isfinite(values)]
            if values.size:
                prt = float(np.median(values))

        feats, fmeta = build_features(
            moments,
            gate_altitude=radar.gate_altitude["data"][sl],
            gate_range=radar.range["data"],
            nyquist=nyquist,
            temperature=temperature,
            freezing_level_m=freezing_level_m,
            texture_window=texture_window,
            elevation=radar.elevation["data"][sl],
            prt=prt,
            trip_ceiling_m=trip_ceiling_m,
            radar_altitude_m=float(np.asarray(radar.altitude["data"]).ravel()[0]),
        )
        temp_source = fmeta["temp_source"]

        sweep_codes, info = single.classify(
            feats,
            shape=fmeta["shape"],
            snr_min=snr_min,
            vel_texture_max=vel_texture_max,
            min_run=min_run,
            despeckle_keep_dbz=despeckle_keep_dbz,
            incoherent_frac=incoherent_frac,
        )

        codes[sl] = sweep_codes.reshape(fmeta["shape"])
        margin[sl] = info["margin"].reshape(fmeta["shape"])
        n_noise += info["n_noise_floor"]
        n_speck += max(info["n_despeckled"], 0)

    for code, name in single.CLASSES.items():
        counts[name] = int((codes == code).sum())

    labels = [single.CLASSES[c] for c in sorted(single.CLASSES)]
    radar.add_field(
        field_name,
        {
            "data": np.ma.masked_array(codes, mask=False),
            "long_name": "Classification of dominant scatterer",
            "standard_name": "gate_id",
            "units": "",
            "flag_values": sorted(single.CLASSES),
            "flag_meanings": " ".join(labels),
            "notes": ",".join(
                f"{c}:{single.CLASSES[c]}" for c in sorted(single.CLASSES)
            ),
            "comment": (
                "Computed from uncorrected moments. Class scores are "
                "normalised by attainable weight budget; gates with no "
                "positive evidence are 0=unclassified rather than a "
                f"silent argmax tie-break. temperature: {temp_source}."
            ),
        },
        replace_existing=replace_existing,
    )

    if add_margin:
        radar.add_field(
            f"{field_name}_margin",
            {
                "data": np.ma.masked_invalid(margin),
                "long_name": "Winning minus runner-up normalised class score",
                "units": "",
                "comment": (
                    "Per-gate confidence. Small values mark gates where "
                    "two classes are nearly tied."
                ),
            },
            replace_existing=replace_existing,
        )

    meta = {
        "resolved": resolved,
        "missing": missing,
        "temp_source": temp_source,
        "nyquist": nyquist,
        "class_counts": counts,
        "skipped_sweeps": skipped,
        "n_noise_floor": n_noise,
        "n_despeckled": n_speck,
        "trip_ceiling_m": trip_ceiling_m,
        "trip_ceiling_source": ceiling_source,
    }
    return to_radar_flavor(radar, output_flavor), meta


def meteorological_gatefilter(radar_like, field_name="gate_id", include=None):
    """Build a :class:`pyart.filters.GateFilter` keeping hydrometeor classes.

    Parameters
    ----------
    radar_like : pyart.core.Radar or xarray.DataTree
        Volume already carrying ``field_name``.
    field_name : str, optional
        Name of the gate-ID field.
    include : sequence of str, optional
        Class names to keep. Defaults to the liquid and frozen classes plus
        ``melting_wet``.

    Returns
    -------
    pyart.filters.GateFilter
        Filter suitable for handing to downstream correction steps.
    """
    import pyart

    radar, _ = to_pyart_radar(radar_like)
    include = include or (single.LIQUID + single.FROZEN + ("melting_wet",))
    gatefilter = pyart.filters.GateFilter(radar)
    gatefilter.exclude_all()
    for name in include:
        gatefilter.include_equal(field_name, single.NAME_TO_CODE[name])
    return gatefilter
