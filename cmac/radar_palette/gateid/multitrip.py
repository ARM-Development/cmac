"""Geometric plausibility of second-trip echo.

Second trip is hard to identify from moments alone, because the signature it
presents -- incoherent phase, low SQI/NCP, noisy rho_hv -- is shared by
receiver noise and by genuinely turbulent weather. Reflectivity texture and
velocity texture both go high in a sheared updraught, so a purely
moment-based test will label real convection as second trip.

Geometry breaks the tie, and does so without ambiguity. An echo appearing at
apparent range ``r`` in the *n*-th trip is truly at ``r + n * r_max``, where
``r_max = c * PRT / 2``. Push that true range through the beam-height equation
at the sweep's elevation and the answer is usually absurd: for a BNF C-SAPR2
volume at PRF 1240 Hz, ``r_max`` is 120.9 km, so a second-trip echo seen at
40 km apparent range is really at 161 km, which at 5.5 deg elevation places it
17 km above the radar and at 12 deg places it 35 km up. Nothing scatters there.

So the rule is: second trip is only *possible* where the second-trip beam is
still low enough to intersect the troposphere. That is a hard geometric veto,
not a tuned threshold, and it depends only on the PRT and the elevation angle
-- both of which the volume already carries.

The echo-top ceiling can be taken from the data rather than assumed. If the
tallest real echo in this volume reaches 17 km, an apparent gate whose
second-trip height exceeds that by a margin cannot be second trip from this
storm.

References
----------
Doviak, R. J., and D. S. Zrnic, 1993: *Doppler Radar and Weather
Observations*, 2nd ed. Academic Press. Range folding and the unambiguous
range.

Zrnic, D. S., and A. V. Ryzhkov, 1999: Polarimetry for weather surveillance
radars. *Bull. Amer. Meteor. Soc.*, 80, 389-406. Second-trip signatures in
polarimetric moments.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "SPEED_OF_LIGHT",
    "beam_height",
    "echo_top_height",
    "volume_echo_top",
    "max_elevation_for_second_trip",
    "second_trip_possible",
    "unambiguous_range",
]

#: Speed of light in m/s.
SPEED_OF_LIGHT = 299792458.0

#: Effective-earth-radius multiplier for standard refraction.
EFFECTIVE_EARTH = 4.0 / 3.0

#: Mean earth radius in m.
EARTH_RADIUS = 6371000.0


def unambiguous_range(prt=None, prf=None):
    """Maximum unambiguous range in metres, ``c * PRT / 2``.

    Parameters
    ----------
    prt : float, optional
        Pulse repetition time in seconds.
    prf : float, optional
        Pulse repetition frequency in Hz. Used if ``prt`` is not given.

    Returns
    -------
    float
        Unambiguous range in metres, or NaN if neither argument is usable.
    """
    if prt is None and prf:
        prt = 1.0 / float(prf)
    if not prt or not np.isfinite(prt) or prt <= 0:
        return np.nan
    return SPEED_OF_LIGHT * float(prt) / 2.0


def beam_height(range_m, elevation_deg, radar_altitude_m=0.0):
    """Beam-centre height above mean sea level under standard refraction.

    Uses the 4/3-earth approximation, which is what operational radar
    processing assumes and is adequate for deciding whether an echo would sit
    in the troposphere or the mesosphere.

    Parameters
    ----------
    range_m : array_like
        Slant range in metres.
    elevation_deg : array_like
        Elevation angle in degrees.
    radar_altitude_m : float, optional
        Radar altitude above mean sea level in metres.

    Returns
    -------
    ndarray
        Height in metres above mean sea level.
    """
    r = np.asarray(range_m, dtype="f8")
    el = np.deg2rad(np.asarray(elevation_deg, dtype="f8"))
    ke_a = EFFECTIVE_EARTH * EARTH_RADIUS
    return (
        np.sqrt(r**2 + ke_a**2 + 2.0 * r * ke_a * np.sin(el)) - ke_a + radar_altitude_m
    )


def echo_top_height(reflectivity, gate_height_m, threshold_dbz=10.0, percentile=99.9):
    """Height of the tallest credible echo in a sweep, in metres.

    Taken as a high percentile rather than the maximum, so a single noisy gate
    aloft cannot raise the ceiling and admit second trip everywhere.

    Parameters
    ----------
    reflectivity : array_like
        Reflectivity in dBZ.
    gate_height_m : array_like
        Gate height above mean sea level, same shape.
    threshold_dbz : float, optional
        Reflectivity above which a gate counts as echo.
    percentile : float, optional
        Percentile of the echo-height distribution to report.

    Returns
    -------
    float
        Height in metres, or NaN if there is no echo.
    """
    z = np.asarray(reflectivity, dtype="f8")
    h = np.asarray(gate_height_m, dtype="f8")
    lit = np.isfinite(z) & np.isfinite(h) & (z >= threshold_dbz)
    if not lit.any():
        return np.nan
    return float(np.percentile(h[lit], percentile))


def volume_echo_top(sweeps, threshold_dbz=10.0, percentile=99.9):
    """Echo top over a whole volume, in metres.

    The ceiling for the second-trip veto must describe the *storm*, not the
    beam. A 1.5 deg sweep cannot see above about 4 km at the ranges it
    samples, so its own echo top is a property of the scan geometry rather
    than of the weather -- on a BNF volume whose storm reached 17.0 km, sweep
    0 reported 3.85 km. Using that as the ceiling vetoes second trip beyond
    ~60 km apparent range on exactly the low sweeps where second trip is most
    likely, which is self-defeating.

    Parameters
    ----------
    sweeps : iterable of (reflectivity, gate_height_m)
        One pair per sweep, each a 2-D array in dBZ and metres MSL.
    threshold_dbz : float, optional
        Reflectivity above which a gate counts as echo.
    percentile : float, optional
        Percentile of the echo-height distribution, per sweep.

    Returns
    -------
    float
        The tallest per-sweep echo top, or NaN if no sweep has echo.
    """
    tops = [echo_top_height(z, h, threshold_dbz, percentile) for z, h in sweeps]
    tops = [t for t in tops if np.isfinite(t)]
    return float(max(tops)) if tops else np.nan


def max_elevation_for_second_trip(
    unambiguous_range_m, ceiling_m, max_range_m, radar_altitude_m=0.0, trip=2
):
    """Highest elevation at which trip-``n`` echo could still be tropospheric.

    Solves ``beam_height(r_apparent + (trip - 1) * r_max, el) <= ceiling`` for
    the elevation, at the *shortest* apparent range in the sweep, which is the
    most permissive case. Above the returned angle no gate in the sweep can be
    second trip.

    Parameters
    ----------
    unambiguous_range_m : float
        ``c * PRT / 2``.
    ceiling_m : float
        Height above which no scatterer is credible -- typically the echo top
        plus a margin.
    max_range_m : float
        Longest gate range in the sweep, used only as a sanity bound.
    radar_altitude_m : float, optional
        Radar altitude above mean sea level.
    trip : int, optional
        Trip number. 2 is second trip.

    Returns
    -------
    float
        Elevation in degrees, 0 if even a horizontal beam is too high, or NaN
        if the inputs are unusable.
    """
    if not np.isfinite(unambiguous_range_m) or not np.isfinite(ceiling_m):
        return np.nan
    folded = (trip - 1) * float(unambiguous_range_m)
    if folded <= 0:
        return np.nan

    # The nearest plausible apparent range gives the lowest second-trip
    # height, so it bounds the elevation most generously.
    r_true = folded + max(float(max_range_m) * 0.02, 1000.0)
    candidates = np.linspace(0.0, 90.0, 1801)
    heights = beam_height(r_true, candidates, radar_altitude_m)
    ok = heights <= ceiling_m
    if not ok.any():
        return 0.0
    return float(candidates[ok][-1])


def second_trip_possible(
    range_m,
    elevation_deg,
    prt=None,
    prf=None,
    ceiling_m=None,
    radar_altitude_m=0.0,
    reflectivity=None,
    gate_height_m=None,
    ceiling_margin_m=3000.0,
    trip=2,
):
    """Boolean mask: gates where trip-``n`` echo is geometrically credible.

    A gate is possible only if the beam, followed out to the *true* range the
    echo would have to occupy, is still at or below ``ceiling_m``. Everything
    else is impossible regardless of how incoherent it looks.

    Parameters
    ----------
    range_m : array_like
        Apparent slant range of each gate, in metres.
    elevation_deg : array_like
        Elevation of each gate, in degrees. Broadcast against ``range_m``.
    prt, prf : float, optional
        Pulse repetition time or frequency, for the unambiguous range.
    ceiling_m : float, optional
        Height above which no scatterer is credible. If not given it is taken
        from the data via :func:`echo_top_height` plus ``ceiling_margin_m``,
        and failing that defaults to 20 km.
    radar_altitude_m : float, optional
        Radar altitude above mean sea level.
    reflectivity, gate_height_m : array_like, optional
        Used to derive the ceiling when ``ceiling_m`` is not supplied.
    ceiling_margin_m : float, optional
        Added to the measured echo top, so a storm slightly taller than the
        one sampled does not get vetoed.
    trip : int, optional
        Trip number to test.

    Returns
    -------
    possible : ndarray of bool
        True where trip-``n`` echo could exist.
    info : dict
        ``unambiguous_range_m``, ``ceiling_m``, ``max_elevation_deg`` and the
        fraction of gates left possible, for reporting.
    """
    r = np.asarray(range_m, dtype="f8")
    el = np.broadcast_to(np.asarray(elevation_deg, dtype="f8"), r.shape)

    r_max = unambiguous_range(prt=prt, prf=prf)
    if not np.isfinite(r_max):
        # Without a PRT nothing can be said, so nothing is vetoed: the moment
        # evidence stands alone rather than being silently overridden.
        return np.ones(r.shape, dtype=bool), {
            "unambiguous_range_m": np.nan,
            "ceiling_m": np.nan,
            "max_elevation_deg": np.nan,
            "fraction_possible": 1.0,
            "note": "no PRT or PRF available; geometric veto not applied",
        }

    if ceiling_m is None:
        top = np.nan
        if reflectivity is not None and gate_height_m is not None:
            top = echo_top_height(reflectivity, gate_height_m)
        ceiling_m = (top + ceiling_margin_m) if np.isfinite(top) else 20000.0

    true_range = r + (trip - 1) * r_max
    height = beam_height(true_range, el, radar_altitude_m)
    possible = height <= ceiling_m

    info = {
        "unambiguous_range_m": float(r_max),
        "ceiling_m": float(ceiling_m),
        "max_elevation_deg": max_elevation_for_second_trip(
            r_max,
            ceiling_m,
            float(np.nanmax(r)) if r.size else 0.0,
            radar_altitude_m,
            trip,
        ),
        "fraction_possible": float(possible.mean()) if possible.size else 0.0,
    }
    return possible, info
