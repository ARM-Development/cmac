"""Feature extraction from a radar volume, for either object family.

Every feature here is derived from *uncorrected* moments, because the gate ID
runs before correction. Nothing in this module may require a ``corrected_*``
field.

Field-name resolution
---------------------
Moment names are not stable across instruments or even across deployment years
of one instrument: BNF C-SAPR2 volumes from 2025 lack the ``uncorrected_``
variants that 2026 volumes carry. Each logical feature is therefore resolved
through an ordered preference list and the winning name is returned in the
metadata, so a field that has silently vanished is an auditable fact rather
than an all-NaN column nobody notices.

Ordering matters: the first match wins, so the shared portion of the Py-ART and
ODIM name lists must agree or the two object families would resolve different
fields from the same volume. A test enforces that.
"""

from __future__ import annotations

import numpy as np

from . import single

__all__ = [
    "FIELD_CANDIDATES",
    "build_features",
    "resolve_fields",
]

#: Logical feature name -> ordered candidate moment names. CfRadial/ARM names
#: come first, then the ODIM short names, so both families agree on the shared
#: block.
FIELD_CANDIDATES = {
    "z": [
        "uncorrected_reflectivity_h",
        "reflectivity_horizontal",
        "reflectivity",
        "DBZ",
        "DBZH",
    ],
    "zdr": [
        "uncorrected_differential_reflectivity",
        "differential_reflectivity",
        "ZDR",
    ],
    "rhohv": [
        "uncorrected_copol_correlation_coeff",
        "copol_correlation_coeff",
        "cross_correlation_ratio",
        "cross_correlation_ratio_hv",
        "RHOHV",
    ],
    "ncp": [
        "uncorrected_normalized_coherent_power",
        "normalized_coherent_power",
        "NCP",
    ],
    "snr": [
        "uncorrected_signal_to_noise_ratio_copolar_h",
        "signal_to_noise_ratio_copolar_h",
        "signal_to_noise_ratio",
        "SNR",
    ],
    "sw": ["uncorrected_spectral_width_h", "spectral_width", "WIDTH", "WRADH"],
    "phidp": ["uncorrected_differential_phase", "differential_phase", "PHIDP"],
    "vel": [
        "uncorrected_mean_doppler_velocity_h",
        "mean_doppler_velocity",
        "velocity",
        "VEL",
        "VRADH",
    ],
}

#: Moments whose along-ray standard deviation is computed. SD(rho_hv) is the
#: strongest non-meteorological discriminant measured on BNF data (Cohen's
#: d = 3.29 against precipitation); SD(PhiDP) is the classical one.
TEXTURE_FIELDS = (
    ("rhohv", "rhohv_texture"),
    ("phidp", "phidp_texture"),
    ("zdr", "zdr_texture"),
    ("z", "z_texture"),
)


def resolve_fields(available, candidates=None):
    """Map logical feature names onto the moments actually present.

    Parameters
    ----------
    available : iterable of str
        Field names present on the volume.
    candidates : dict, optional
        Override for :data:`FIELD_CANDIDATES`.

    Returns
    -------
    resolved : dict
        Logical name -> the moment name that will be used.
    missing : list of str
        Logical names with no candidate present.
    """
    candidates = FIELD_CANDIDATES if candidates is None else candidates
    have = set(available)
    resolved, missing = {}, []
    for short, names in candidates.items():
        for name in names:
            if name in have:
                resolved[short] = name
                break
        else:
            missing.append(short)
    return resolved, missing


def build_features(
    moments,
    gate_altitude,
    gate_range,
    nyquist=None,
    temperature=None,
    freezing_level_m=None,
    texture_window=4,
    elevation=None,
    prt=None,
    radar_altitude_m=0.0,
    trip_ceiling_m=None,
):
    """Assemble the feature dictionary the classifier consumes.

    Parameters
    ----------
    moments : dict of str to ndarray
        Logical feature name -> 2-D array shaped (ray, gate). Keys follow
        :data:`FIELD_CANDIDATES`; missing moments are simply absent.
    gate_altitude : ndarray
        Gate altitude in metres above mean sea level, shaped like the moments.
    gate_range : ndarray
        Slant range in metres, broadcastable to the moment shape.
    nyquist : float, optional
        Nyquist velocity in m/s. Required for folding-aware velocity texture;
        without it the velocity features are omitted rather than computed
        wrongly.
    temperature : ndarray, optional
        Gate temperature in degrees Celsius. Strongly preferred over
        ``freezing_level_m`` alone.
    freezing_level_m : float, optional
        Height of the 0 degC level in metres MSL. Used for height-over-isotherm
        and, if ``temperature`` is absent, for a 6.5 K/km lapse-rate estimate
        that is flagged as such in the returned metadata.
    texture_window : int, optional
        Footprint, in gates and rays, of the texture operator.
    elevation : array_like, optional
        Elevation of each ray in degrees. Enables the geometric second-trip
        veto; without it ``trip_possible`` is not produced and the multi-trip
        class rests on moment evidence alone.
    prt : float, optional
        Pulse repetition time in seconds, for the unambiguous range.
    radar_altitude_m : float, optional
        Radar altitude above mean sea level.
    trip_ceiling_m : float, optional
        Height above which no scatterer is credible, for the second-trip veto.
        Should be derived from the whole VOLUME: a low sweep's own echo top
        reflects how high its beam reaches, not how tall the storm is, and
        using it vetoes second trip precisely where it is most likely. When
        omitted the ceiling falls back to this sweep's echo top, which is
        correct only for a single-sweep input such as an RHI.

    Returns
    -------
    features : dict of str to ndarray
        Flattened 1-D feature arrays.
    meta : dict
        ``shape``, ``nyquist``, ``temp_source`` and the derived feature names.
    """
    if "z" not in moments:
        raise ValueError("reflectivity ('z') is required")
    shape = np.asarray(moments["z"]).shape

    feats = {}
    for key, arr in moments.items():
        feats[key] = np.asarray(arr, dtype="f8").ravel()

    height = np.broadcast_to(np.asarray(gate_altitude, dtype="f8"), shape)
    rng = np.broadcast_to(np.asarray(gate_range, dtype="f8"), shape)
    feats["height_km"] = (height / 1000.0).ravel()
    feats["range_km"] = (rng / 1000.0).ravel()

    for short, key in TEXTURE_FIELDS:
        if short in moments:
            feats[key] = single.texture(
                np.asarray(moments[short], dtype="f8"), texture_window
            ).ravel()

    if "zdr" in moments and "rhohv" in moments:
        feats["dr"] = single.depolarization_ratio(
            np.asarray(moments["zdr"], dtype="f8"),
            np.asarray(moments["rhohv"], dtype="f8"),
        ).ravel()

    if (
        "vel" in moments
        and nyquist is not None
        and np.isfinite(nyquist)
        and nyquist > 0
    ):
        vel = np.asarray(moments["vel"], dtype="f8")
        vtex = single.angular_texture(vel, nyquist, texture_window)
        feats["vel_texture"] = vtex.ravel()
        feats["vel_norm"] = (np.abs(vel) / nyquist).ravel()
        # Normalised by the uniform-random-phase limit, so the membership
        # functions are independent of PRF and transfer between radars.
        feats["vel_texture_norm"] = (vtex / (nyquist / np.sqrt(3.0))).ravel()

    # Geometric plausibility of second trip. Without a PRT this is all-ones,
    # so the moment evidence stands alone rather than being silently
    # overridden by a veto that could not be evaluated.
    if elevation is not None:
        from .multitrip import second_trip_possible

        possible, trip_meta = second_trip_possible(
            rng,
            np.broadcast_to(np.asarray(elevation, dtype="f8").reshape(-1, 1), shape),
            prt=prt,
            ceiling_m=trip_ceiling_m,
            radar_altitude_m=radar_altitude_m,
            reflectivity=np.asarray(moments["z"], dtype="f8"),
            gate_height_m=height,
        )
        feats["trip_possible"] = possible.astype("f8").ravel()
    else:
        trip_meta = None

    temp_source = "none"
    if temperature is not None:
        feats["temp"] = np.broadcast_to(
            np.asarray(temperature, dtype="f8"), shape
        ).ravel()
        temp_source = "provided"
    elif freezing_level_m is not None:
        feats["temp"] = ((freezing_level_m - height) * 6.5e-3).ravel()
        temp_source = "lapse_rate_from_freezing_level"

    if freezing_level_m is not None:
        feats["hoi0_km"] = ((height - freezing_level_m) / 1000.0).ravel()

    meta = {
        "shape": shape,
        "nyquist": nyquist,
        "temp_source": temp_source,
        "freezing_level_m": freezing_level_m,
        "second_trip": trip_meta,
        "derived": sorted(set(feats) - set(moments)),
    }
    return feats, meta
