"""Single-volume gate identification.

Per-gate classification of the dominant scatterer from polarimetric moments,
computed from a single radar volume with no reference to any other. This is the
memoryless baseline; :mod:`radar_palette.gateid.temporal` builds on it.

The classifier is intended for processing chains that identify gates *before*
correction, where the gate ID is not a diagnostic product but the control flow:
it selects which gates reach phase processing, attenuation correction, velocity
dealiasing and rainfall estimation. A defect here is silent and propagates.

Design decisions worth knowing
------------------------------
**Scores are normalised by attainable weight budget.** In a plain additive fuzzy
scheme a class can only win if the evidence it *could* muster is competitive.
Profiling an operational configuration on 4.75 million gates showed ``rain``
reaching at most 3.0 without a sounding while ``snow`` reached 4.0, so snow took
84% of gates above 40 dBZ in warm-season convection. No amount of
membership-function tuning fixes that; the budget itself is the bug.

**A class must have its evidence present to be eligible.** Budget normalisation
alone lets a class score a perfect 1.0 on two of five terms and tie one that
satisfied all of its own. See :data:`MIN_EVIDENCE_COVERAGE`.

**Gates with no positive evidence are ``unclassified``, never class zero.**
``argmax`` breaks ties toward index 0, silently.

**Phase coherence, not an arbitrary threshold, identifies incoherent echo.** A
magnetron randomises transmit phase pulse to pulse, so second-trip echo and
receiver noise both have radial velocity uniformly distributed over the Nyquist
interval, giving a texture of ``v_nyq/sqrt(3)``. See
:data:`INCOHERENT_TEXTURE_FRAC`.

References
----------
Park, H. S., A. V. Ryzhkov, D. S. Zrnic, and K.-E. Kim, 2009: The hydrometeor
classification algorithm for the polarimetric WSR-88D. *Wea. Forecasting*, 24,
730-748, doi:10.1175/2008WAF2222205.1. Source of the melting-layer hard
constraints.

Ryzhkov, A., S. Y. Matrosov, V. Melnikov, D. Zrnic, P. Zhang, Q. Cao, M. Knight,
C. Simmer, and S. Troemel, 2017: Estimation of depolarization ratio using
weather radars with simultaneous transmission/reception. *J. Appl. Meteor.
Climatol.*, 56, 1797-1816, doi:10.1175/JAMC-D-16-0098.1. Source of
:func:`depolarization_ratio`.

Zrnic, D. S., A. V. Ryzhkov, J. M. Straka, Y. Liu, and J. Vivekanandan, 2001:
Testing a procedure for automatic classification of hydrometeor types.
*J. Atmos. Oceanic Technol.*, 18, 892-913. Establishes that Z and ZDR combined
carry the strongest discriminating power.
"""

from __future__ import annotations

import numpy as np

# Integer codes are part of the file format; append, never renumber.
CLASSES = {
    0: "unclassified",
    1: "no_scatter",
    2: "clutter",
    3: "biological",
    4: "multi_trip",
    5: "light_rain",
    6: "moderate_rain",
    7: "heavy_rain",
    8: "melting_wet",
    9: "ice_snow",
    10: "graupel_hail",
}
NAME_TO_CODE = {v: k for k, v in CLASSES.items()}

NON_MET = ("no_scatter", "clutter", "biological", "multi_trip")
LIQUID = ("light_rain", "moderate_rain", "heavy_rain")
FROZEN = ("ice_snow", "graupel_hail")


def trapmf(x, pts):
    """Trapezoidal membership, matching ``skfuzzy.trapmf``.

    1 on [b, c], linear ramps on [a, b) and (c, d], 0 elsewhere. NaN maps to 0
    so a missing field contributes no evidence rather than propagating NaN.
    """
    a, b, c, d = (float(v) for v in pts)
    x = np.asarray(x, dtype="f8")
    y = np.zeros_like(x)
    if b > a:
        m = (x > a) & (x < b)
        y[m] = (x[m] - a) / (b - a)
    if d > c:
        m = (x > c) & (x < d)
        y[m] = (d - x[m]) / (d - c)
    y[(x >= b) & (x <= c)] = 1.0
    y[~np.isfinite(x)] = 0.0
    return y


def depolarization_ratio(zdr_db, rhohv):
    """Depolarization ratio (dB) from SHV moments -- Ryzhkov et al. 2017, Eq. 6.

    A radar transmitting horizontal and vertical polarizations simultaneously
    cannot measure circular depolarization ratio directly, but

        DR = (1 + Zdr^-1 - 2 rho_hv Zdr^-1/2)
             / (1 + Zdr^-1 + 2 rho_hv Zdr^-1/2)

    with ``Zdr`` in linear units is a proxy for CDR computable from the
    standard moments. It behaves like LDR without needing a cross-polar
    channel: it rises sharply for irregular, randomly oriented, wet or
    tumbling scatterers.

    Reference: Ryzhkov, A., S. Y. Matrosov, V. Melnikov, D. Zrnic, P. Zhang,
    Q. Cao, M. Knight, C. Simmer and S. Troemel, 2017: Estimation of
    Depolarization Ratio Using Weather Radars with Simultaneous
    Transmission/Reception. *J. Appl. Meteor. Climatol.*, 56, 1797-1816,
    doi:10.1175/JAMC-D-16-0098.1.

    Measured on a BNF C-SAPR2 RHI, restricted to coherent gates with real
    signal (median values):

        biology (ZDR > 3 dB, rho_hv < 0.9, T > 5 C)   -5.3 dB
        near-range low-velocity clutter               -9.6 dB
        precipitation (Z >= 25 dBZ, rho_hv > 0.97)   -19.6 dB
        anvil ice (T < -15 C, rho_hv > 0.97)         -19.4 dB

    A ~14 dB separation between biology and hydrometeors, which is why this
    is weighted heavily in the biological membership function.
    """
    zdr_db = np.asarray(zdr_db, dtype="f8")
    rho_in = np.asarray(rhohv, dtype="f8")
    rho = np.clip(rho_in, 0.0, 1.0)
    zl = np.power(10.0, zdr_db / 10.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = 1.0 / zl
        s = np.sqrt(inv)
        num = 1.0 + inv - 2.0 * rho * s
        den = 1.0 + inv + 2.0 * rho * s
        out = 10.0 * np.log10(np.clip(num / den, 1e-12, None))
    # np.where rather than boolean assignment, so scalar inputs work too.
    return np.where(np.isfinite(zdr_db) & np.isfinite(rho_in), out, np.nan)


def texture(field, window=4):
    """NaN-aware standard-deviation texture over a ``window`` square footprint.

    Py-ART offers :func:`pyart.util.texture` and
    :func:`pyart.util.texture_along_ray`, and neither fits here: both take a
    :class:`~pyart.core.Radar` rather than an array, both compute a 1-D
    standard deviation along the ray rather than over a 2-D footprint, and
    ``pyart.util.texture`` hardcodes an 11-point window and prints to stdout.
    This classifier needs a 2-D footprint on a bare array, sized to match the
    velocity texture it is compared against.

    The NaN handling is the substantive difference. Gates with fewer than three
    valid neighbours return NaN rather than a value computed from almost
    nothing, so an isolated sample cannot manufacture texture.
    """
    from scipy import ndimage

    data = np.asarray(field, dtype="f8")
    valid = np.isfinite(data).astype("f8")
    filled = np.where(np.isfinite(data), data, 0.0)
    n = ndimage.uniform_filter(valid, size=window, mode="nearest") * window**2
    s1 = ndimage.uniform_filter(filled, size=window, mode="nearest") * window**2
    s2 = ndimage.uniform_filter(filled**2, size=window, mode="nearest") * window**2
    with np.errstate(invalid="ignore", divide="ignore"):
        var = s2 / n - (s1 / n) ** 2
    out = np.sqrt(np.clip(var, 0.0, None))
    out[n < 3] = np.nan
    return out


def angular_texture(vel, nyquist, window=4):
    """Folding-aware velocity texture, delegating to Py-ART.

    A plain standard deviation across the +/-Nyquist branch cut reports a huge
    spread for perfectly coherent flow, so the statistic must be computed on
    the unit circle. :func:`pyart.util.angular_texture_2d` does exactly that,
    and is used here rather than reimplemented: on a real BNF sweep the two
    agree to a median absolute difference of 7e-15.

    The only thing added is NaN propagation. Py-ART convolves with
    ``boundary="symm"``, which lets a NaN spread through the whole window and,
    on the same sweep, leaves 2% of gates finite that should not be. Here a
    gate is NaN if it has fewer than three valid neighbours, matching
    :func:`texture` so the two are comparable.
    """
    import pyart

    v = np.asarray(vel, dtype="f8")
    if not np.isfinite(nyquist) or nyquist <= 0:
        return texture(v, window)

    size = (window, window) if isinstance(window, int) else tuple(window)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.asarray(
            pyart.util.angular_texture_2d(
                np.nan_to_num(v, nan=0.0), size, float(nyquist)
            ),
            dtype="f8",
        )

    from scipy import ndimage

    valid = np.isfinite(v).astype("f8")
    n = ndimage.uniform_filter(valid, size=size, mode="nearest") * float(np.prod(size))
    out[n < 3] = np.nan
    out[~np.isfinite(v)] = np.nan
    return out


# Membership functions over uncorrected moments and derived textures.
# key -> [[a, b, c, d], weight]
MEMBERSHIP = {
    "no_scatter": {
        "snr": [[-100, -100, 2, 5], 3.0],
        "z": [[-100, -100, -8, -2], 2.0],
        "rhohv": [[0, 0, 0.5, 0.7], 1.0],
        # Receiver noise is phase-incoherent for the same reason second trip
        # is, so it also sits at the uniform-phase texture limit. What
        # separates the two is returned power, handled by the SNR terms.
        "vel_texture_norm": [[0.22, 0.40, 1.2, 1.2], 2.0],
    },
    "clutter": {
        "dr": [[-16.0, -12.0, 0.0, 0.0], 1.5],
        "vel_norm": [[0, 0, 0.03, 0.08], 3.0],
        "sw": [[0, 0, 1.0, 1.8], 1.5],
        "rhohv": [[0.2, 0.4, 0.85, 0.92], 1.5],
        "range_km": [[0, 0, 12.0, 25.0], 1.5],
        "rhohv_texture": [[0.03, 0.08, 1.0, 1.0], 1.0],
    },
    "biological": {
        # Depolarization ratio (Ryzhkov et al. 2017) separates biology from
        # hydrometeors by ~14 dB on BNF data -- a wider margin than any single
        # standard moment -- so it carries the most weight here.
        "dr": [[-14.0, -10.0, 0.0, 0.0], 3.5],
        "zdr": [[2.0, 3.5, 12.0, 15.0], 3.0],
        "rhohv": [[0.3, 0.5, 0.85, 0.93], 2.0],
        "rhohv_texture": [[0.03, 0.08, 1.0, 1.0], 2.5],
        "z": [[-15, -8, 18, 25], 2.0],
        "sw": [[1.0, 1.8, 6.0, 8.0], 1.0],
        "phidp_texture": [[20, 40, 200, 200], 1.5],
        "zdr_texture": [[0.5, 1.0, 6.0, 8.0], 1.5],
        "z_texture": [[1.5, 3.0, 20.0, 25.0], 1.0],
        # Insects and birds do not fly in subfreezing air. This term plus the
        # hard constraint below keeps biology out of the cold cloud, where its
        # noisy-rhohv/high-ZDR signature would otherwise mimic ice.
        "temp": [[3.0, 6.0, 100, 100], 2.5],
    },
    "multi_trip": {
        # Second-trip echo from a magnetron radar is *incoherent*: the
        # transmitter's starting phase is random pulse to pulse, so a target
        # beyond the unambiguous range is phase-scrambled and its apparent
        # radial velocity is uniformly distributed over +/-Nyquist. The
        # standard deviation of a uniform distribution on that interval is
        # v_nyq/sqrt(3) -- 9.4 m/s at BNF's 16.3 m/s Nyquist -- and the
        # measured noise/second-trip population sits exactly there (median
        # 8.96 m/s). First-trip weather is phase-coherent and measures
        # 0.74 m/s. That is a 12x separation and the single most reliable
        # discriminant available, so it dominates this class.
        #
        # The membership therefore ramps in from ~40% of the uniform-phase
        # limit and saturates at it. ``vel_texture_norm`` (texture divided by
        # Nyquist) is used where available so the same numbers transfer to a
        # radar with a different PRF; plain ``vel_texture`` is the fallback.
        "vel_texture_norm": [[0.22, 0.40, 1.2, 1.2], 4.0],
        # Real returned power is the ONLY thing separating second trip from
        # receiver noise -- both are phase-incoherent and sit at the same
        # texture limit. The ramp starts above the noise floor and this term
        # carries weight comparable to the coherence term, so a gate without
        # power cannot be called second trip.
        "snr": [[3.0, 8.0, 1000, 1000], 3.5],
        "ncp": [[0, 0, 0.5, 0.65], 1.5],
        "rhohv": [[0, 0, 0.7, 0.85], 1.5],
        "rhohv_texture": [[0.05, 0.10, 1.0, 1.0], 1.0],
        "phidp_texture": [[40, 60, 200, 200], 1.0],
    },
    "light_rain": {
        "dr": [[-60.0, -60.0, -14.0, -10.0], 1.0],
        "z": [[0, 5, 25, 32], 2.0],
        "rhohv": [[0.95, 0.97, 1, 1], 2.0],
        "rhohv_texture": [[0, 0, 0.02, 0.05], 1.5],
        "zdr": [[-0.5, -0.2, 1.5, 2.5], 1.0],
        "temp": [[0.0, 2.0, 100, 100], 2.0],
    },
    "moderate_rain": {
        "dr": [[-60.0, -60.0, -14.0, -10.0], 1.0],
        "z": [[25, 30, 45, 50], 2.0],
        "rhohv": [[0.95, 0.97, 1, 1], 2.0],
        "rhohv_texture": [[0, 0, 0.02, 0.05], 1.5],
        "zdr": [[0.2, 0.5, 3.0, 4.0], 1.0],
        "temp": [[0.0, 2.0, 100, 100], 2.0],
    },
    "heavy_rain": {
        "dr": [[-60.0, -60.0, -14.0, -10.0], 1.0],
        "z": [[42, 47, 70, 70], 2.5],
        "rhohv": [[0.93, 0.96, 1, 1], 2.0],
        "zdr": [[0.5, 1.0, 4.5, 6.0], 1.0],
        "temp": [[0.0, 2.0, 100, 100], 2.0],
    },
    "melting_wet": {
        # The melting layer is thin and sits just below the 0 C level. Wet
        # growth does not begin until a particle is already descending through
        # near-freezing air, so the temperature window is narrow and centred
        # slightly warm of 0 C. A wide window let this class claim the whole
        # anvil, which is physically wrong: at -20 C nothing is melting.
        "rhohv": [[0.80, 0.85, 0.95, 0.97], 3.0],
        "zdr": [[0.5, 1.0, 4.0, 5.0], 1.5],
        "z": [[20, 25, 50, 55], 1.0],
        "temp": [[-2.0, -0.5, 2.5, 4.0], 4.0],
        # Melting particles are wet and irregular: depressed rhohv WITH low
        # texture. High rhohv texture means noise or biology, not a bright band.
        "rhohv_texture": [[0, 0, 0.03, 0.06], 1.5],
    },
    "ice_snow": {
        "dr": [[-60.0, -60.0, -14.0, -10.0], 1.0],
        "rhohv": [[0.93, 0.96, 1, 1], 1.5],
        "zdr": [[-0.5, -0.2, 1.0, 1.8], 1.0],
        "z": [[-5, 0, 35, 42], 1.0],
        # Everything colder than about -1 C is ice. This is the anvil: a broad,
        # confident plateau rather than a narrow window, so ice wins there
        # instead of melting or hail.
        "temp": [[-100, -100, -1.0, 1.0], 4.0],
        "rhohv_texture": [[0, 0, 0.03, 0.06], 1.0],
    },
    "graupel_hail": {
        # Hail and graupel require a genuinely strong core. Without the Z floor
        # this class leaked into the weak-echo anvil.
        "z": [[45, 50, 70, 70], 3.0],
        "zdr": [[-1.0, -0.5, 1.0, 1.5], 1.5],
        "rhohv": [[0.92, 0.95, 1, 1], 1.0],
        "temp": [[-100, -100, 5.0, 10.0], 1.0],
    },
}

#: SNR above which an incoherent gate is treated as a real distant target
#: rather than receiver noise, and so is left for the classifier to label as
#: second trip instead of being gated out as no_scatter.
TRIP_SNR_MIN = 8.0


# [class, feature, (lo, hi)] -> zero the score inside the interval.
HARD_CONSTRAINTS = [
    # Park et al. 2009: snow is not permitted below the melting layer, and
    # rain is not permitted above its top. Big drops are the documented
    # exception, lofted above the freezing level in convective updraughts;
    # heavy_rain is therefore left unconstrained aloft.
    #
    # NOTE: an earlier revision wrote this constraint as
    # ["ice_snow", "hoi0_km", (0.5, 1e6)], which forbade ice ABOVE the
    # freezing level -- the exact opposite of the intent, and the reason the
    # storm anvil was coming out as melting or hail. Ice is forbidden well
    # BELOW the melting layer, where it has had time to melt.
    ["ice_snow", "hoi0_km", (-1e6, -1.5)],
    ["light_rain", "hoi0_km", (1.0, 1e6)],
    ["moderate_rain", "hoi0_km", (1.5, 1e6)],
    # Melting is a narrow band around the 0 C level. Nothing melts at -5 C, and
    # nothing is still melting several degrees into the warm sector.
    ["melting_wet", "temp", (5.0, 1e6)],
    ["melting_wet", "temp", (-1e6, -5.0)],
    ["melting_wet", "hoi0_km", (-1e6, -2.5)],
    ["melting_wet", "hoi0_km", (1.5, 1e6)],
    # Biology cannot exist in subfreezing air. Insects and birds are confined
    # to the warm boundary layer; without this the class captured anvil ice,
    # whose noisy rhohv and positive ZDR look superficially similar.
    ["biological", "temp", (-1e6, 3.0)],
    ["biological", "z", (30.0, 1e6)],
    ["biological", "height_km", (6.0, 1e6)],
    # Hail requires a strong core; it must not claim weak anvil echo.
    ["graupel_hail", "z", (-1e6, 40.0)],
    ["clutter", "z", (45.0, 1e6)],
    ["clutter", "height_km", (4.0, 1e6)],
    ["multi_trip", "z", (35.0, 1e6)],
    # Geometry, not tuning: where second trip is impossible the class is
    # forbidden outright. ``trip_possible`` is 1 where the folded beam could
    # still be in the troposphere and 0 where it could not, so the constraint
    # zeroes multi_trip on the impossible half. See
    # :mod:`radar_palette.gateid.multitrip`.
    ["multi_trip", "trip_possible", (-1e6, 0.5)],
]


#: Velocity texture, as a fraction of the uniform-random-phase limit
#: v_nyq/sqrt(3), above which a gate is treated as phase-incoherent. Measured
#: on BNF RHIs: receiver noise sits at 0.95 (median 8.96 of 9.41 m/s) while
#: precipitation sits at 0.08 (0.74 m/s). A cut at 0.32 rejected 100% of noise
#: while keeping 99.9% of gates with Z >= 25 dBZ and rho_hv > 0.95.
INCOHERENT_TEXTURE_FRAC = 0.32


def noise_floor_mask(
    features,
    snr_min=3.0,
    snr_taper=1.0,
    vel_texture_max=None,
    ncp_min=None,
    incoherent_frac=INCOHERENT_TEXTURE_FRAC,
    keep_dbz=None,
    trip_snr_min=TRIP_SNR_MIN,
):
    """Gates that are not a coherent measurement of a scatterer.

    Py-ART's noise helpers solve a different problem:
    :func:`pyart.retrieve.calculate_snr_from_reflectivity` and
    :func:`pyart.retrieve.compute_snr` *derive* SNR, and
    :func:`pyart.correct.calc_noise_floor` estimates a receiver noise level
    from the data. This consumes an SNR that already exists and decides
    membership, so it composes with those rather than replacing them: if a
    volume lacks an SNR field, compute one with Py-ART and pass it in.

    Speckle outside the storm is mostly receiver noise that happens to land in
    some class's membership region. Rather than let the fuzzy scores arbitrate
    that, such gates are forced to ``no_scatter`` up front.

    Two independent tests, because they fail on different things:

    ``snr_min``
        Power-based. Rejects gates below the minimum detectable signal.
    ``incoherent_frac``
        Phase-based, and the stronger of the two. A coherent target produces a
        smooth radial-velocity field; receiver noise -- and, on a magnetron
        radar, second-trip echo -- has random phase, so its velocity is
        uniformly distributed over +/-Nyquist and its texture approaches
        v_nyq/sqrt(3). Gates above ``incoherent_frac`` of that limit are not
        first-trip weather. This is what removes speckle that passes the SNR
        test, which the power-based cut alone cannot do.

    ``keep_dbz`` protects strong echo from both tests, so a bright core is
    never blanked by a texture artefact at its edge.
    """
    n = len(next(iter(features.values())))
    mask = np.zeros(n, dtype=bool)

    if snr_min is not None and "snr" in features and features["snr"] is not None:
        snr = np.asarray(features["snr"], dtype="f8")
        mask |= np.isfinite(snr) & (snr < snr_min - snr_taper)
    if ncp_min is not None and "ncp" in features:
        ncp = np.asarray(features["ncp"], dtype="f8")
        mask |= np.isfinite(ncp) & (ncp < ncp_min)

    # Explicit absolute threshold in m/s, if the caller supplied one.
    if vel_texture_max is not None and "vel_texture" in features:
        vt = np.asarray(features["vel_texture"], dtype="f8")
        mask |= np.isfinite(vt) & (vt > vel_texture_max)

    # Normalised phase-coherence test, PRF-independent.
    #
    # Incoherence alone does NOT mean no scatterer. Receiver noise and
    # second-trip echo are both phase-incoherent -- that is the whole reason
    # the coherence test works -- and the only thing separating them is
    # returned power. Gating on incoherence without excepting powered gates
    # made multi_trip unreachable: it scored 1.0 and was then overwritten with
    # no_scatter before the label was ever emitted.
    if incoherent_frac is not None and "vel_texture_norm" in features:
        vtn = np.asarray(features["vel_texture_norm"], dtype="f8")
        incoherent = np.isfinite(vtn) & (vtn > incoherent_frac)
        if trip_snr_min is not None and "snr" in features:
            powered = np.asarray(features["snr"], dtype="f8")
            incoherent &= ~(np.isfinite(powered) & (powered >= trip_snr_min))
        mask |= incoherent

    if keep_dbz is not None and "z" in features:
        zz = np.asarray(features["z"], dtype="f8")
        mask &= ~(np.isfinite(zz) & (zz >= keep_dbz))
    return mask


def despeckle(codes, shape, min_run=3, axis=1, protect=(), keep_mask=None):
    """Remove runs shorter than ``min_run`` along a ray.

    Not a substitute for :func:`pyart.correct.despeckle_field`, and not a
    reimplementation of it. That function thresholds a *continuous* field,
    finds 2-D connected objects and returns a
    :class:`~pyart.filters.GateFilter` marking small ones for exclusion. This
    operates on the *categorical* class field after classification, dissolving
    short runs of one label surrounded by another, and returns labels rather
    than a mask. Both are useful; they answer different questions, and the
    Py-ART one is the right tool for speckle in reflectivity.

    An isolated one- or two-gate island of some class inside a different
    background is not a resolvable scatterer -- the pulse volume is larger than
    that -- so it is noise or a classifier artefact. Runs shorter than
    ``min_run`` are replaced by the neighbouring label where the neighbours
    agree, and by ``no_scatter`` otherwise.

    ``keep_mask`` protects gates that must never be dissolved regardless of run
    length. This matters: a two-gate 50 dBZ core at the edge of a cell is a real
    scatterer, and blanket despeckling removed 20% of gates above 30 dBZ on a
    BNF RHI before this guard existed. Callers should pass a reflectivity
    threshold mask.

    Operating along the range axis is deliberate: it is the axis with uniform,
    fine sampling in both PPI and RHI geometry, whereas the across-beam axis is
    azimuth in one and elevation in the other.
    """
    if min_run <= 1:
        return codes
    grid = codes.reshape(shape).copy()
    keep = (
        np.zeros(shape, dtype=bool)
        if keep_mask is None
        else np.asarray(keep_mask, dtype=bool).reshape(shape)
    )
    if axis == 0:
        grid, keep = grid.T, keep.T
    protect = {NAME_TO_CODE.get(p, p) if isinstance(p, str) else p for p in protect}

    n_rays, n_gates = grid.shape
    for i in range(n_rays):
        row, krow = grid[i], keep[i]
        start = 0
        for j in range(1, n_gates + 1):
            if j < n_gates and row[j] == row[start]:
                continue
            run = j - start
            val = row[start]
            if (
                run < min_run
                and val != 0
                and val not in protect
                and not krow[start:j].any()
            ):
                left = row[start - 1] if start > 0 else None
                right = row[j] if j < n_gates else None
                if left is not None and right is not None and left == right:
                    row[start:j] = left
                else:
                    row[start:j] = NAME_TO_CODE["no_scatter"]
            start = j
    if axis == 0:
        grid = grid.T
    return grid.ravel()


#: A class must have at least this fraction of its total weight backed by
#: features that are actually present, or it is not eligible. Budget
#: normalisation alone lets a class score a perfect 1.0 on two of five terms
#: and tie a class that satisfied all of its own -- so a gate with no range or
#: spectrum width could be called ``clutter`` on rho_hv alone.
MIN_EVIDENCE_COVERAGE = 0.5


def _budget(terms, available):
    b = sum(w for k, (_, w) in terms.items() if k in available)
    return b if b > 0 else 1.0


def _coverage(terms, available):
    """Fraction of a class's total weight that its available features carry."""
    total = sum(w for _, (_, w) in terms.items())
    if total <= 0:
        return 1.0
    return sum(w for k, (_, w) in terms.items() if k in available) / total


def classify(
    features,
    membership=None,
    hard_constraints=None,
    classes=None,
    return_scores=False,
    shape=None,
    snr_min=3.0,
    vel_texture_max=None,
    min_run=3,
    despeckle_keep_dbz=30.0,
    incoherent_frac=INCOHERENT_TEXTURE_FRAC,
    min_coverage=MIN_EVIDENCE_COVERAGE,
    score_adjusters=(),
):
    """Classify gates from a dict of 1-D feature arrays.

    Returns ``(codes, info)``. ``codes`` are the integer codes of
    :data:`CLASSES`; ``info`` carries the normalised score matrix, the winning
    score, the margin over the runner-up and the class order.

    Three speckle controls, applied in this order:

    ``snr_min``
        Gates below the minimum detectable signal become ``no_scatter``
        before the fuzzy scores are consulted. Set to ``None`` to disable.
    ``vel_texture_max``
        Absolute texture cut in m/s, if you want one. Normally leave this None
        and use ``incoherent_frac`` instead, which is PRF-independent.
    ``incoherent_frac``
        Velocity texture as a fraction of the uniform-random-phase limit
        v_nyq/sqrt(3), above which a gate is phase-incoherent and cannot be
        first-trip weather. This is the main speckle control; the SNR floor
        alone leaves incoherent gates that happen to carry power.
    ``min_run``
        After classification, runs shorter than this along the ray are
        dissolved. Requires ``shape``. Set to 1 to disable.
    ``despeckle_keep_dbz``
        Gates at or above this reflectivity are never dissolved, whatever the
        run length. Without it, ``min_run=3`` removed 20% of gates above
        30 dBZ on a BNF RHI.
    """
    membership = MEMBERSHIP if membership is None else membership
    hard_constraints = (
        HARD_CONSTRAINTS if hard_constraints is None else hard_constraints
    )
    order = (
        list(classes)
        if classes
        else [c for c in CLASSES.values() if c != "unclassified"]
    )
    order = [c for c in order if c in membership]

    available = {k for k, v in features.items() if v is not None}
    n = len(next(iter(features.values())))
    scores = np.zeros((n, len(order)), dtype="f8")

    covered = []
    for j, cls in enumerate(order):
        terms = membership[cls]
        # A class whose defining evidence is mostly absent is not eligible.
        # Without this, budget normalisation lets it score 1.0 on whatever
        # happens to be present and tie a fully-evidenced class.
        if _coverage(terms, available) < min_coverage:
            covered.append(False)
            continue
        covered.append(True)
        s = np.zeros(n)
        for key, (pts, w) in terms.items():
            if key not in available or w == 0:
                continue
            s += trapmf(features[key], pts) * w
        # Normalise by attainable budget so a class cannot win merely by
        # having more evidence terms defined for it.
        scores[:, j] = s / _budget(terms, available)

    for cls, key, (lo, hi) in hard_constraints:
        if cls not in order or key not in available:
            continue
        v = np.asarray(features[key], dtype="f8")
        scores[(v >= lo) & (v <= hi), order.index(cls)] = 0.0

    # Score adjustments (e.g. temporal priors) are applied HERE: after the
    # hard constraints, so a prior can never resurrect a class that physics
    # forbids, and before the argmax, so everything downstream -- the
    # unclassified rule, the noise floor and despeckling -- applies to the
    # adjusted answer exactly as it does to the instantaneous one.
    n_adjusted = 0
    if score_adjusters:
        part0 = np.partition(scores, -2, axis=1) if scores.shape[1] > 1 else scores
        margin0 = scores.max(axis=1) - (
            part0[:, -2] if scores.shape[1] > 1 else np.zeros(n)
        )
        before_scores = scores
        for adjust in score_adjusters:
            scores = adjust(scores, order, margin0)
        # Re-apply the constraints: an adjuster is not permitted to lift a
        # class the geometry or thermodynamics ruled out.
        for cls, key, (lo, hi) in hard_constraints:
            if cls not in order or key not in available:
                continue
            v = np.asarray(features[key], dtype="f8")
            scores[(v >= lo) & (v <= hi), order.index(cls)] = 0.0
        n_adjusted = int((scores != before_scores).any(axis=1).sum())

    best = scores.argmax(axis=1)
    top = scores[np.arange(n), best]
    part = np.partition(scores, -2, axis=1) if scores.shape[1] > 1 else scores
    second = part[:, -2] if scores.shape[1] > 1 else np.zeros(n)

    codes = np.array([NAME_TO_CODE[order[i]] for i in best], dtype="i2")
    codes[top <= 0] = 0  # explicit unclassified, never a silent tie-break

    n_noise = n_speck = 0
    if snr_min is not None or vel_texture_max is not None or incoherent_frac:
        noise = noise_floor_mask(
            features,
            snr_min=snr_min,
            vel_texture_max=vel_texture_max,
            incoherent_frac=incoherent_frac,
            keep_dbz=despeckle_keep_dbz,
        )
        n_noise = int(noise.sum())
        codes[noise] = NAME_TO_CODE["no_scatter"]

    if min_run and min_run > 1 and shape is not None:
        before = codes.copy()
        # Never dissolve a strong core, however short the run: a two-gate
        # 50 dBZ return at a cell edge is a real scatterer, not speckle.
        keep = None
        if despeckle_keep_dbz is not None and "z" in features:
            zz = np.asarray(features["z"], dtype="f8")
            keep = np.isfinite(zz) & (zz >= despeckle_keep_dbz)
        codes = despeckle(
            codes, shape, min_run=min_run, protect=("no_scatter",), keep_mask=keep
        )
        n_speck = int((codes != before).sum())
    elif min_run and min_run > 1:
        # Despeckling is a spatial operation and needs the sweep geometry. A
        # bare feature dict has none, so skip it and say so rather than either
        # failing or silently pretending it ran.
        n_speck = -1

    info = {
        "scores": scores,
        "order": order,
        "top_score": top,
        "margin": top - second,
        "n_noise_floor": n_noise,
        "n_despeckled": n_speck,
        "n_score_adjusted": n_adjusted,
        "ineligible": [c for c, ok in zip(order, covered, strict=True) if not ok],
    }
    return codes, info
