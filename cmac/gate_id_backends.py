"""
cmac.gate_id_backends
=====================

Alternative dominant-scatterer classifiers for the CMAC ``gate_id`` field.

    radar_palette_available
    radar_palette_gate_id
    sounding_freezing_level
    build_classification_radar
    fold_to_cmac_categories

CMAC's own classifier is :func:`cmac.cmac_processing.do_my_fuzz`: five
trapezoidal membership classes scored additively, argmax per gate. This module
adds a second backend that delegates the classification to
``radar_palette.gateid``, an eleven-class scheme with its own noise-floor,
second-trip and despeckle logic, and folds its answer back onto the five
categories CMAC's downstream code consumes.

Why a fold rather than a wider ``gate_id``
------------------------------------------
Everything downstream of classification in :func:`cmac.cmac_radar.cmac` reads
the category vocabulary out of the field's ``notes`` attribute, and
:func:`cmac.gate_id.get_gate_id_categories` derives each category's integer
code from its *position* in that string. Two places also read codes as bare
literals: the Z-PHI phase-processing gate filter includes ``gate_id`` 1 and 2
(rain and snow). Widening the code space, or reordering it, would therefore
silently repoint those literals at different classes. So the published
``gate_id`` keeps CMAC's exact five-category order and the eleven-class result
is published alongside it, in full, as ``scatterer_classification`` with CF
``flag_values``/``flag_meanings``. Nothing downstream changes meaning; the
extra detail is additive.

The evidence guard
------------------
``radar_palette.gateid.single.classify`` decides which features a class may be
scored on by testing whether a feature *key* is present, not whether its value
at a given gate is finite (``single._budget``, and the ``available`` set built
in ``single.classify``). Gate temperature and height-over-freezing-level are
derived from gate geometry, so they are finite at every gate, including gates
where no moment was measured at all. An empty-sky gate can therefore score
above zero on temperature alone and be labelled ice or rain: on one BNF
C-SAPR2 volume 1,073,535 such gates were labelled, and on a NEXRAD surveillance
volume 8.4 million, nine times the validly labelled population.

In CMAC that is not a cosmetic problem. The ``gate_id`` field is the single
authoritative mask: it sets the gates used for velocity dealiasing, for the
Z-PHI attenuation and KDP path, and for all three rain-rate estimators. A
hydrometeor label on a gate with no measurement would propagate into a
rainfall total. This backend therefore requires at least one finite *measured*
moment at a gate before any hydrometeor label survives, and forces
``no_scatter`` elsewhere. The count of gates so demoted is reported in the
returned metadata as ``n_no_evidence``.

"""

import copy
import warnings

import numpy as np

#: CMAC's five fuzzy categories, in the order :func:`cmac.cmac_processing.do_my_fuzz`
#: emits them, which is the order that fixes their integer codes. ``cmac()``
#: appends ``clutter`` (5) and ``terrain_blockage`` (6) after classification
#: when it has the inputs to do so; this backend never invents either, so the
#: positional ``notes`` contract is preserved exactly.
CMAC_GATE_ID_CATEGORIES = ('multi_trip', 'rain', 'snow', 'no_scatter', 'melting')

#: Default fold from ``radar_palette.gateid`` class names onto CMAC categories.
#:
#: The three rain intensities collapse to ``rain`` and the two frozen classes to
#: ``snow`` because that is the distinction CMAC's rain-rate and snow-rate gates
#: draw. ``biological`` and ``clutter`` fold to ``no_scatter``: CMAC's own
#: ``clutter`` category is code 5 and exists only when a ground-clutter field or
#: a vendor classification mask was supplied, so claiming it here would either
#: create a gap in the ``notes`` positions or duplicate a label. Both classes
#: remain readable in full in the ``scatterer_classification`` field, and both
#: are excluded from meteorological gates either way, which is what the fold is
#: for. ``unclassified`` means the classifier found no class scoring above zero,
#: which is the same operational statement as ``no_scatter``.
RADAR_PALETTE_TO_CMAC = {
    'unclassified': 'no_scatter',
    'no_scatter': 'no_scatter',
    'clutter': 'no_scatter',
    'biological': 'no_scatter',
    'multi_trip': 'multi_trip',
    'light_rain': 'rain',
    'moderate_rain': 'rain',
    'heavy_rain': 'rain',
    'melting_wet': 'melting',
    'ice_snow': 'snow',
    'graupel_hail': 'snow',
}

#: Logical moment -> the field name this module publishes it under on the
#: classification radar handed to ``radar_palette``. Each is a member of the
#: matching ``radar_palette.gateid.features.FIELD_CANDIDATES`` list, and because
#: the classification radar carries exactly one candidate per logical moment,
#: resolution is unambiguous rather than left to the classifier's own
#: preference order. What that single candidate *contains* is decided by
#: :data:`UNCORRECTED_CANDIDATES` below.
CLASSIFICATION_FIELD_NAMES = {
    'z': 'reflectivity',
    'zdr': 'differential_reflectivity',
    'rhohv': 'cross_correlation_ratio',
    'ncp': 'normalized_coherent_power',
    'snr': 'signal_to_noise_ratio',
    'sw': 'spectral_width',
    'phidp': 'differential_phase',
    'vel': 'mean_doppler_velocity',
}

#: Logical moment -> ordered names of the *uncorrected* moment on an ARM
#: volume, tried before the per-radar ``field_names`` entry.
#:
#: Classification runs on uncorrected moments by convention: the unprefixed
#: fields on an ARM ``a1`` volume have already had vendor processing applied
#: -- clutter filtering, thresholding, and on the CACTI and TRACER generations
#: attenuation correction -- and what that processing did differs across sites
#: and instrument generations, while the uncorrected moments are the same
#: measurement everywhere. Every ARM C-SAPR2 ``a1`` volume examined (BNF 2026,
#: CACTI 2018, TRACER 2022) publishes the first six of these; NCP and SNR are
#: published uncorrected only at BNF, and legacy platforms (MDV-era X-SAPR,
#: NEXRAD) publish none of them, so each moment falls back to the name the
#: radar's ``field_names`` config gives -- which keeps the config the single
#: source of truth wherever the uncorrected moment does not exist.
#:
#: Spectrum width has no ``field_names`` key at all, because CMAC's own fuzzy
#: classifier does not use it while ``radar_palette`` weights it in the
#: clutter, biological and second-trip classes, so its fallbacks are listed
#: here too: ``spectrum_width`` is Py-ART's name on MDV and NEXRAD volumes,
#: ``spectral_width`` on modern ARM CfRadial.
UNCORRECTED_CANDIDATES = {
    'z': ('uncorrected_reflectivity_h', 'uncorrected_reflectivity'),
    'zdr': ('uncorrected_differential_reflectivity',),
    'rhohv': ('uncorrected_copol_correlation_coeff',
              'uncorrected_cross_correlation_ratio'),
    'ncp': ('uncorrected_normalized_coherent_power',),
    'snr': ('uncorrected_signal_to_noise_ratio_copolar_h',
            'uncorrected_signal_to_noise_ratio'),
    'sw': ('uncorrected_spectral_width_h', 'uncorrected_spectral_width',
           'spectral_width', 'spectrum_width'),
    'phidp': ('uncorrected_differential_phase',),
    'vel': ('uncorrected_mean_doppler_velocity_h',
            'uncorrected_mean_doppler_velocity'),
}

#: Per-radar calibration offsets, and which logical moment each applies to.
#: ``cmac()`` adds these in place to the *configured* reflectivity and ZDR
#: fields before classification, so when this module substitutes the
#: uncorrected moment it has to add them itself or the classifier would score
#: an uncalibrated instrument. They are not applied when a moment falls back
#: to the configured field, which ``cmac()`` has already offset.
CALIBRATION_OFFSETS = {'z': 'ref_offset', 'zdr': 'zdr_offset'}

#: Gate temperature below which ``sounding_temperature`` is treated as a fill
#: value rather than a measurement. ``cmac()`` fills the masked entries of the
#: mapped sounding profile with -9999, which is finite and, read as a
#: temperature, is cold enough to make every such gate ice.
_TEMPERATURE_FILL_FLOOR = -500.0


def radar_palette_available():
    """Return True if ``radar_palette.gateid`` can be imported."""
    try:
        import radar_palette.gateid  # noqa: F401
    except ImportError:
        return False
    return True


def _import_radar_palette():
    """Import and return the ``radar_palette.gateid`` entry points.

    Raised as an ``ImportError`` with an actionable message rather than a bare
    ``ModuleNotFoundError`` from somewhere deep in the VAP, because selecting
    this backend is a configuration choice and the fix is an install.
    """
    try:
        from radar_palette.gateid import entry_points, single
    except ImportError as err:
        raise ImportError(
            "gate_id_method='radar_palette' requires radar_palette.gateid, "
            "which CMAC does not depend on: it is imported only when a radar "
            "configuration selects this backend. The gateid module is not in "
            "radar-palette's released main branch yet -- install from the "
            "gateid development branch (pip install "
            "'radar-palette @ git+https://github.com/scollis/radar-palette"
            "@gateid'), or set gate_id_method='cmac_fuzzy' in the radar "
            "configuration to use CMAC's own fuzzy classifier."
        ) from err
    return entry_points, single


def sounding_freezing_level(radar, temperature_field='sounding_temperature',
                            min_temperature=-30.0):
    """
    Height of the 0 degC level in metres MSL, from the gate sounding
    temperature.

    Returns the lowest gate altitude at which the mapped sounding temperature
    is below freezing but above ``min_temperature``. This is the same
    ``fzl_sounding`` term :func:`cmac.cmac_processing.get_melt` computes, split
    out because it is needed *before* classification: ``get_melt`` blends the
    sounding estimate with the altitude of the melting-class gates, so it
    cannot run until a ``gate_id`` field exists, while ``radar_palette``'s
    melting-layer hard constraints want a freezing level as an input. The
    lower bound excludes the cold gates high in the volume, whose altitudes
    would otherwise be candidates for the minimum.

    Returns None if the sounding covers no sub-freezing gate, in which case the
    caller should classify without melting-layer constraints rather than guess.

    """
    temperature = np.ma.masked_less(
        radar.fields[temperature_field]['data'], _TEMPERATURE_FILL_FLOOR)
    sub_freezing = np.ma.filled(
        (temperature > min_temperature) & (temperature < 0.0), False)
    if not sub_freezing.any():
        return None
    return float(radar.gate_altitude['data'][sub_freezing].min())


def build_classification_radar(radar, field_config, cmac_config=None):
    """
    Return a shallow view of ``radar`` carrying only the moments to classify
    on, renamed to :data:`CLASSIFICATION_FIELD_NAMES`.

    Three things this does, all of them the point of doing it at all:

    1. Each moment is taken from the *uncorrected* field where the volume
       publishes one (:data:`UNCORRECTED_CANDIDATES`), falling back to the
       radar's ``field_names`` entry otherwise. Classification is a judgement
       about what the instrument measured, so it runs on the measurement, not
       on fields that carry vendor clutter filtering, thresholding or
       attenuation correction whose definition varies by site and instrument
       generation.
    2. Exactly one candidate per logical moment is published, so
       ``radar_palette.gateid.features.resolve_fields`` cannot silently pick a
       different field than the one intended -- it walks its own ordered
       preference list, which on an ARM a1 volume has several live options per
       moment.
    3. The per-radar calibration offsets are applied to the uncorrected
       reflectivity and ZDR (:data:`CALIBRATION_OFFSETS`), because ``cmac()``
       applies them in place to the *configured* fields and an uncorrected
       moment has not been through that. The sounding fill value is dropped
       (see ``_TEMPERATURE_FILL_FLOOR``).

    The returned object is a shallow copy: the geometry, instrument parameters
    and sweep metadata are shared with the caller's radar, and only ``fields``
    is replaced, so nothing here can perturb the volume being processed.

    Parameters
    ----------
    radar : Radar
        The volume being processed.
    field_config : dict
        Per-radar field-name mapping, from :func:`cmac.config.get_field_names`.
    cmac_config : dict, optional
        Per-radar processing values. Read for the calibration offsets and for
        ``gate_id_apply_offsets``; when omitted, offsets are not applied.

    Returns
    -------
    classification_radar : Radar
        The view to hand to the classifier.
    moment_fields : list of str
        Names, on the returned view, of the *measured* moments -- the fields
        the evidence guard tests for finiteness. Gate temperature is not among
        them; that is the whole point of the guard.
    resolved : dict
        Logical moment -> the source field name actually used, so a caller can
        report which generation of moment each site ended up classifying on.

    """
    cmac_config = {} if cmac_config is None else cmac_config
    configured = {
        'z': field_config['reflectivity'],
        'zdr': field_config.get(
            'differential_reflectivity', field_config.get('input_zdr')),
        'rhohv': field_config['cross_correlation_ratio'],
        'ncp': field_config['normalized_coherent_power'],
        # cmac() guarantees this field, either copied from the configured SNR
        # field or computed from reflectivity when the config names none.
        'snr': 'signal_to_noise_ratio',
        'sw': field_config.get('spectral_width'),
        'phidp': field_config['input_phidp_field'],
        'vel': field_config['velocity'],
    }

    apply_offsets = cmac_config.get('gate_id_apply_offsets', True)
    fields = {}
    moment_fields = []
    resolved = {}
    for logical, fallback in configured.items():
        source = next((name for name in UNCORRECTED_CANDIDATES[logical]
                       if name in radar.fields), None)
        is_uncorrected = source is not None
        if source is None:
            source = fallback
        if source is None or source not in radar.fields:
            continue

        target = CLASSIFICATION_FIELD_NAMES[logical]
        field = radar.fields[source]
        offset_key = CALIBRATION_OFFSETS.get(logical)
        offset = cmac_config.get(offset_key) if offset_key else None
        if is_uncorrected and apply_offsets and offset:
            # Copy first: the offset must not reach the volume being
            # processed, which carries the offset on its own configured field.
            field = dict(field)
            field['data'] = field['data'] + offset
        fields[target] = field
        moment_fields.append(target)
        resolved[logical] = source

    # Gate temperature and height are derived, not measured, so they are
    # published for the classifier to use but deliberately left out of
    # moment_fields.
    if 'sounding_temperature' in radar.fields:
        temperature = dict(radar.fields['sounding_temperature'])
        temperature['data'] = np.ma.masked_less(
            temperature['data'], _TEMPERATURE_FILL_FLOOR)
        fields['sounding_temperature'] = temperature

    classification_radar = copy.copy(radar)
    classification_radar.fields = fields
    return classification_radar, moment_fields, resolved


#: Fraction of gates left ``unclassified`` above which the run is reported as
#: a classification failure rather than as a result. The classifier declines
#: whole sweeps it judges unsuitable -- an RHI whose elevation span is too
#: narrow, for instance -- and returns ``unclassified`` for every gate in
#: them. Folded onto CMAC's categories that becomes ``no_scatter``, which is
#: indistinguishable from clear air: the VAP would emit a file whose every
#: masked product is empty, with nothing in it saying why. Measured on TRACER
#: C-SAPR2 cell-tracking RHIs, where four volumes of 16 to 76 rays and
#: elevation spans of 19 degrees were skipped in full.
UNCLASSIFIED_WARN_FRACTION = 0.5


def _report_unclassified(codes, unclassified_code, meta, cmac_config,
                         verbose=False):
    """Surface a classification the backend should not present as clear air.

    Returns the count of ``unclassified`` gates and the classifier's list of
    skipped sweeps. Raises or warns per ``gate_id_unclassified_policy``
    ('warn', the default, or 'error' for a production run that should fail
    rather than write an empty mask).
    """
    n_unclassified = int((codes == unclassified_code).sum())
    fraction = n_unclassified / codes.size
    skipped = list(meta.get('skipped_sweeps') or [])
    if not skipped and fraction <= UNCLASSIFIED_WARN_FRACTION:
        return n_unclassified, skipped

    reasons = '; '.join(
        'sweep %s (%s, elevation span %.1f deg)'
        % (entry.get('sweep'), entry.get('sweep_mode'),
           float(entry.get('elevation_span', float('nan'))))
        for entry in skipped) or 'no sweep was reported as skipped'
    message = (
        "radar_palette left %d of %d gates (%.1f%%) unclassified: %s. Folded "
        "onto CMAC's categories those gates become no_scatter, so every "
        "masked product in this volume would be empty or near-empty without "
        "saying why. Classify this volume with gate_id_method='cmac_fuzzy', "
        "or set gate_id_unclassified_policy='error' to make this a hard "
        "failure." % (n_unclassified, codes.size, 100.0 * fraction, reasons))

    policy = cmac_config.get('gate_id_unclassified_policy', 'warn')
    if policy == 'error':
        raise RuntimeError(message)
    if policy != 'warn':
        raise ValueError(
            "gate_id_unclassified_policy must be 'warn' or 'error', not %r"
            % (policy,))
    warnings.warn(message, UserWarning)
    if verbose:
        print('##    UNCLASSIFIED: %s' % reasons)
    return n_unclassified, skipped


def _no_evidence_mask(classification_radar, moment_fields):
    """Boolean mask of gates at which no measured moment is finite."""
    has_evidence = np.zeros(
        (classification_radar.nrays, classification_radar.ngates), dtype=bool)
    for name in moment_fields:
        data = classification_radar.fields[name]['data']
        has_evidence |= np.isfinite(np.ma.filled(data, np.nan))
    return ~has_evidence


def fold_to_cmac_categories(codes, classes, class_map=None):
    """
    Fold ``radar_palette`` integer class codes onto CMAC's category codes.

    Parameters
    ----------
    codes : ndarray of int
        Per-gate ``radar_palette.gateid`` class codes.
    classes : dict
        ``radar_palette.gateid.single.CLASSES``, i.e. code -> class name.
    class_map : dict, optional
        Class name -> CMAC category name. Defaults to
        :data:`RADAR_PALETTE_TO_CMAC`. Every value must be one of
        :data:`CMAC_GATE_ID_CATEGORIES`; a value outside it would put a code in
        the ``gate_id`` field that the positional ``notes`` contract cannot
        describe.

    Returns
    -------
    folded : ndarray of int
        Per-gate CMAC category codes.
    fold_counts : dict
        ``radar_palette`` class name -> number of gates, for the classes that
        occurred. Kept because the fold is lossy and this is the record of what
        was folded away.

    """
    class_map = RADAR_PALETTE_TO_CMAC if class_map is None else class_map

    unknown = sorted(set(class_map) - set(classes.values()))
    if unknown:
        raise ValueError(
            "gate_id_class_map names classes that radar_palette does not "
            "define: %s. Known classes: %s"
            % (unknown, sorted(classes.values())))
    unmapped = sorted(set(classes.values()) - set(class_map))
    if unmapped:
        raise ValueError(
            "gate_id_class_map does not say what to do with the radar_palette "
            "classes %s. Every class must be mapped, so that no gate is left "
            "with an undefined category." % unmapped)
    bad_targets = sorted(
        set(class_map.values()) - set(CMAC_GATE_ID_CATEGORIES))
    if bad_targets:
        raise ValueError(
            "gate_id_class_map maps onto categories CMAC's gate_id field does "
            "not define: %s. Valid targets are %s. The clutter (5) and "
            "terrain_blockage (6) categories are added by cmac() itself when "
            "it has the inputs for them and cannot be assigned here."
            % (bad_targets, list(CMAC_GATE_ID_CATEGORIES)))

    category_code = {name: i for i, name in enumerate(CMAC_GATE_ID_CATEGORIES)}
    # Build a lookup table indexed by radar_palette code so the fold is one
    # vectorised take() rather than a mask per class.
    lookup = np.zeros(max(classes) + 1, dtype='i2')
    for code, name in classes.items():
        lookup[code] = category_code[class_map[name]]

    folded = lookup[codes]
    fold_counts = {
        classes[code]: int(count)
        for code, count in zip(*np.unique(codes, return_counts=True))
    }
    return folded, fold_counts


def radar_palette_gate_id(radar, field_config, cmac_config, verbose=False):
    """
    Classify gates with ``radar_palette.gateid`` and fold onto CMAC categories.

    Parameters
    ----------
    radar : Radar
        Radar object part-way through :func:`cmac.cmac_radar.cmac`: it must
        already carry ``sounding_temperature``, ``height`` and
        ``signal_to_noise_ratio``, because those are what the classifier scores
        the thermodynamic and noise-floor terms on.
    field_config : dict
        Per-radar field-name mapping, from :func:`cmac.config.get_field_names`.
    cmac_config : dict
        Per-radar processing values, from :func:`cmac.config.get_cmac_values`.
        Read here: ``gate_id_class_map``, ``gate_id_freezing_level``,
        ``gate_id_apply_offsets``, ``ref_offset``, ``zdr_offset``,
        ``gate_id_snr_min``, ``gate_id_min_run``, ``gate_id_despeckle_keep_dbz``,
        ``gate_id_incoherent_frac``, ``gate_id_texture_window``,
        ``gate_id_publish_margin``.
    verbose : bool
        Print the resolved fields, temperature provenance and class counts.

    Returns
    -------
    gid : dict
        ``gate_id`` field dictionary, in CMAC's five-category code space, with
        the positional ``notes`` string the rest of the VAP parses.
    categories : tuple of str
        The category names, in code order.
    extra_fields : dict
        Field dictionaries to add alongside ``gate_id``:
        ``scatterer_classification`` always, and
        ``scatterer_classification_margin`` when
        ``gate_id_publish_margin`` is true.
    meta : dict
        The classifier's own metadata, plus ``n_no_evidence`` (gates demoted by
        the evidence guard), ``fold_counts`` and ``freezing_level_m``.

    """
    entry_points, single = _import_radar_palette()

    classification_radar, moment_fields, resolved = build_classification_radar(
        radar, field_config, cmac_config)
    if verbose:
        print('##    classifying on: %s'
              % ', '.join('%s=%s' % (logical, source)
                          for logical, source in sorted(resolved.items())))

    # None means "take the classifier's own default", which is not the same as
    # passing None through: that would switch the phase-coherence test off
    # altogether. 0 is the documented way to disable it.
    incoherent_frac = cmac_config.get('gate_id_incoherent_frac')
    if incoherent_frac is None:
        incoherent_frac = single.INCOHERENT_TEXTURE_FRAC

    freezing_level_m = cmac_config.get('gate_id_freezing_level')
    if freezing_level_m is None:
        freezing_level_m = sounding_freezing_level(radar)
    if freezing_level_m is None and verbose:
        print('##    no sub-freezing sounding gate; melting-layer hard '
              'constraints disabled')

    classified, meta = entry_points.gate_id(
        classification_radar,
        freezing_level_m=freezing_level_m,
        # The mapped sounding profile is a real measurement of the thermal
        # structure and is strongly preferred over the classifier's lapse-rate
        # fallback, which only knows the freezing level.
        temperature_field='sounding_temperature',
        field_name='scatterer_classification',
        add_margin=True,
        texture_window=cmac_config.get('gate_id_texture_window', 4),
        snr_min=cmac_config.get('gate_id_snr_min', 3.0),
        min_run=cmac_config.get('gate_id_min_run', 3),
        despeckle_keep_dbz=cmac_config.get(
            'gate_id_despeckle_keep_dbz', 30.0),
        incoherent_frac=incoherent_frac,
        replace_existing=True,
    )
    # gate_id() returns a new radar object rather than mutating the one it was
    # given, so the classification is read off the return value. The two
    # families store rays in different rotational order and a mask built
    # against the wrong one agrees only ~76% of the time, so the ray
    # correspondence is checked rather than assumed -- cheap next to the cost
    # of silently mis-registered sector statistics.
    if not np.allclose(np.asarray(classified.azimuth['data'], dtype='f8'),
                       np.asarray(radar.azimuth['data'], dtype='f8'),
                       equal_nan=True):
        raise RuntimeError(
            'radar_palette returned a volume whose rays are not in the order '
            'they were supplied in; the classification cannot be attached to '
            'this radar object gate for gate.')
    detail = classified.fields['scatterer_classification']
    codes = np.ma.filled(detail['data'], 0).astype('i2')

    # Whether the classifier actually classified. Checked before the evidence
    # guard and the fold, both of which turn unclassified gates into
    # no_scatter and would hide a declined volume.
    n_unclassified, skipped_sweeps = _report_unclassified(
        codes, single.NAME_TO_CODE['unclassified'], meta, cmac_config,
        verbose=verbose)

    # The evidence guard. See the module docstring: the classifier's own
    # coverage test is per-feature-key, not per-gate, so a gate with no
    # measurement at all can still carry a hydrometeor label.
    no_evidence = _no_evidence_mask(classification_radar, moment_fields)
    n_no_evidence = int((codes[no_evidence]
                         != single.NAME_TO_CODE['no_scatter']).sum())
    codes[no_evidence] = single.NAME_TO_CODE['no_scatter']

    # A config may name only the classes it wants routed differently; the rest
    # keep the documented default, so a YAML override does not have to restate
    # all eleven.
    class_map = dict(RADAR_PALETTE_TO_CMAC)
    class_map.update(cmac_config.get('gate_id_class_map') or {})
    folded, fold_counts = fold_to_cmac_categories(
        codes, single.CLASSES, class_map)

    gid = {
        'data': folded,
        'units': '',
        'long_name': 'Classification of dominant scatterer',
        'notes': ','.join('%d:%s' % (i, name) for i, name
                          in enumerate(CMAC_GATE_ID_CATEGORIES)),
        'valid_min': 0,
        'valid_max': len(CMAC_GATE_ID_CATEGORIES) - 1,
        'comment': (
            'Folded from the radar_palette gate-ID classification published '
            'in scatterer_classification; see that field for the full class '
            'set.'),
    }

    class_codes = sorted(single.CLASSES)
    detail = dict(detail)
    detail['data'] = codes
    detail['units'] = ''
    detail['long_name'] = (
        'Classification of dominant scatterer, radar_palette gate-ID classes')
    detail['flag_values'] = class_codes
    detail['flag_meanings'] = ' '.join(
        single.CLASSES[code] for code in class_codes)
    detail['valid_min'] = class_codes[0]
    detail['valid_max'] = class_codes[-1]
    detail['temperature_source'] = str(meta.get('temp_source'))
    if freezing_level_m is not None:
        detail['freezing_level_m'] = float(np.round(freezing_level_m, 2))
    extra_fields = {'scatterer_classification': detail}

    if cmac_config.get('gate_id_publish_margin', False):
        margin = classified.fields.get('scatterer_classification_margin')
        if margin is not None:
            extra_fields['scatterer_classification_margin'] = margin

    meta = dict(meta)
    meta['classified_on'] = resolved
    meta['n_unclassified'] = n_unclassified
    meta['skipped_sweeps'] = skipped_sweeps
    meta['n_no_evidence'] = n_no_evidence
    meta['fold_counts'] = fold_counts
    meta['freezing_level_m'] = freezing_level_m

    if verbose:
        print('##    temperature source: %s' % meta.get('temp_source'))
        if meta.get('missing'):
            print('##    moments absent: %s' % sorted(meta['missing']))
        if meta.get('skipped_sweeps'):
            print('##    sweeps left unclassified: %d'
                  % len(meta['skipped_sweeps']))
        print('##    gates demoted by the evidence guard: %d' % n_no_evidence)
        for name, count in sorted(
                fold_counts.items(), key=lambda kv: -kv[1]):
            print('##      %-14s %9d -> %s'
                  % (name, count, class_map[name]))

    return gid, CMAC_GATE_ID_CATEGORIES, extra_fields, meta
