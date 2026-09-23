"""Unit tests for the alternative gate-ID backends.

These build their radars with ``pyart.testing`` rather than downloading a
volume, so the whole module runs offline. The tests that need the classifier
itself skip when ``radar_palette`` is not installed, since CMAC does not
depend on it.
"""

import sys
import warnings

import numpy as np
import pyart
import pytest

from cmac.gate_id import get_gate_id_categories
from cmac.gate_id_backends import (
    CMAC_GATE_ID_CATEGORIES,
    RADAR_PALETTE_TO_CMAC,
    build_classification_radar,
    fold_to_cmac_categories,
    radar_palette_available,
    sounding_freezing_level,
    _import_radar_palette,
)

# radar_palette's own class table, restated here so a change to it upstream
# shows up as a failing test rather than as a silently different fold.
RADAR_PALETTE_CLASSES = {
    0: 'unclassified',
    1: 'no_scatter',
    2: 'clutter',
    3: 'biological',
    4: 'multi_trip',
    5: 'light_rain',
    6: 'moderate_rain',
    7: 'heavy_rain',
    8: 'melting_wet',
    9: 'ice_snow',
    10: 'graupel_hail',
}

# The field names the BNF C-SAPR2 config uses, which is the mapping the
# backend is expected to honour instead of the classifier's own preference
# order.
FIELD_CONFIG = {
    'reflectivity': 'reflectivity',
    'differential_reflectivity': 'differential_reflectivity',
    'input_zdr': 'differential_reflectivity',
    'cross_correlation_ratio': 'copol_correlation_coeff',
    'normalized_coherent_power': 'normalized_coherent_power',
    'input_phidp_field': 'differential_phase',
    'velocity': 'mean_doppler_velocity',
    'signal_to_noise_ratio': 'signal_to_noise_ratio_copolar_h',
}


def _field(data, units='1'):
    return {'data': np.ma.asarray(data), 'units': units,
            'long_name': 'test field'}


@pytest.fixture
def radar():
    """A small PPI volume carrying both corrected and uncorrected moments.

    Gate 0 of every ray is left masked in every measured moment, so the
    evidence guard has something to catch, and the sounding temperature is
    filled with -9999 there exactly as ``cmac()`` fills it.
    """
    radar = pyart.testing.make_empty_ppi_radar(20, 36, 2)
    # make_empty_ppi_radar spaces gates one metre apart, which puts the whole
    # volume within a few metres of the radar and leaves no vertical structure
    # for a temperature profile to sit in. 500 m gates and two real elevation
    # angles give a volume 10 km deep in range and a few km deep in altitude.
    radar.range['data'] = np.arange(radar.ngates, dtype='f8') * 500.0
    radar.elevation['data'][:36] = 1.0
    radar.elevation['data'][36:] = 20.0
    radar.fixed_angle['data'][:] = [1.0, 20.0]
    radar.init_gate_altitude()
    shape = (radar.nrays, radar.ngates)

    def measured(value):
        """A moment measured everywhere except gate 0 of every ray."""
        data = np.ma.masked_all(shape)
        data[:, 1:] = value
        return data

    reflectivity = measured(30.0)
    velocity = measured(2.0)
    snr = measured(25.0)

    # Each moment is published twice: the vendor-processed name and the
    # uncorrected one, with values that differ enough for a test to tell which
    # was used but stay in the same physical regime so the class a gate lands
    # in does not depend on that choice.
    radar.add_field('reflectivity', _field(reflectivity, 'dBZ'))
    radar.add_field('uncorrected_reflectivity_h',
                    _field(reflectivity - 10.0, 'dBZ'))
    radar.add_field('copol_correlation_coeff', _field(measured(0.99)))
    radar.add_field('uncorrected_copol_correlation_coeff',
                    _field(measured(0.985)))
    radar.add_field('differential_reflectivity',
                    _field(measured(0.5), 'dB'))
    radar.add_field('uncorrected_differential_reflectivity',
                    _field(measured(0.2), 'dB'))
    radar.add_field('normalized_coherent_power', _field(measured(0.8)))
    radar.add_field('differential_phase', _field(measured(0.0), 'deg'))
    radar.add_field('uncorrected_differential_phase',
                    _field(measured(1.0), 'deg'))
    radar.add_field('mean_doppler_velocity', _field(velocity, 'm/s'))
    radar.add_field('uncorrected_mean_doppler_velocity_h',
                    _field(velocity + 0.1, 'm/s'))
    radar.add_field('signal_to_noise_ratio_copolar_h', _field(snr, 'dB'))
    # cmac() copies the configured SNR field to this name before classifying.
    radar.add_field('signal_to_noise_ratio', _field(snr, 'dB'))
    radar.add_field('spectral_width', _field(measured(0.5), 'm/s'))
    radar.add_field('uncorrected_spectral_width_h',
                    _field(measured(0.6), 'm/s'))

    # A profile that crosses 0 degC part-way up the volume, with cmac()'s
    # -9999 fill on the gates where the mapped sounding was masked.
    altitude = radar.gate_altitude['data']
    freezing_altitude = float(np.median(altitude))
    temperature = np.where(altitude > freezing_altitude, -5.0, 10.0)
    temperature[:, 0] = -9999.0
    radar.freezing_altitude = freezing_altitude
    radar.add_field('sounding_temperature', _field(temperature, 'degC'))
    radar.add_field('height', _field(radar.gate_altitude['data'].copy(), 'm'))
    return radar


def test_every_class_is_mapped():
    """The default fold must name every class radar_palette can emit."""
    assert set(RADAR_PALETTE_TO_CMAC) == set(RADAR_PALETTE_CLASSES.values())
    assert set(RADAR_PALETTE_TO_CMAC.values()) <= set(CMAC_GATE_ID_CATEGORIES)


def test_fold_follows_the_documented_grouping():
    codes = np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], dtype='i2')
    folded, counts = fold_to_cmac_categories(codes, RADAR_PALETTE_CLASSES)
    category = {name: i for i, name in enumerate(CMAC_GATE_ID_CATEGORIES)}
    expected = [category[RADAR_PALETTE_TO_CMAC[RADAR_PALETTE_CLASSES[c]]]
                for c in range(11)]
    assert folded.tolist() == [expected]
    # The three rain intensities and the two frozen classes are the lossy part
    # of the fold, so the per-class counts are what preserves them.
    assert counts['light_rain'] == counts['heavy_rain'] == 1
    assert folded[0, 5] == folded[0, 6] == folded[0, 7] == category['rain']
    assert folded[0, 9] == folded[0, 10] == category['snow']


def test_fold_codes_agree_with_the_notes_contract():
    """The codes the fold emits must match what the notes string declares.

    ``cmac.gate_id.get_gate_id_categories`` derives each category's code from
    its *position* in the notes string, and two gate filters downstream read
    codes 1 and 2 as literals, so this is the contract that keeps the
    published field interpretable.
    """
    notes = ','.join('%d:%s' % (i, name)
                     for i, name in enumerate(CMAC_GATE_ID_CATEGORIES))
    categories = get_gate_id_categories({'notes': notes})
    assert categories['rain'] == 1
    assert categories['snow'] == 2
    codes = np.array([[7, 9]], dtype='i2')  # heavy_rain, ice_snow
    folded, _ = fold_to_cmac_categories(codes, RADAR_PALETTE_CLASSES)
    assert folded.tolist() == [[categories['rain'], categories['snow']]]


def test_fold_rejects_a_target_outside_the_five_categories():
    class_map = dict(RADAR_PALETTE_TO_CMAC, clutter='clutter')
    with pytest.raises(ValueError, match='clutter'):
        fold_to_cmac_categories(
            np.zeros((1, 1), dtype='i2'), RADAR_PALETTE_CLASSES, class_map)


def test_fold_rejects_an_incomplete_map():
    class_map = {'no_scatter': 'no_scatter'}
    with pytest.raises(ValueError, match='Every class must be mapped'):
        fold_to_cmac_categories(
            np.zeros((1, 1), dtype='i2'), RADAR_PALETTE_CLASSES, class_map)


def test_fold_rejects_an_unknown_class_name():
    class_map = dict(RADAR_PALETTE_TO_CMAC, drizzle='rain')
    with pytest.raises(ValueError, match='drizzle'):
        fold_to_cmac_categories(
            np.zeros((1, 1), dtype='i2'), RADAR_PALETTE_CLASSES, class_map)


def test_classification_radar_prefers_the_uncorrected_moments(radar):
    """Classification runs on the measurement, not the vendor-processed field.

    The fixture's uncorrected reflectivity sits 10 dB below the unprefixed
    field, so which one was used is visible in the values.
    """
    classification_radar, moment_fields, resolved = build_classification_radar(
        radar, FIELD_CONFIG)

    # Exactly one candidate per logical moment, so radar_palette's own
    # preference order cannot pick a different field.
    assert 'uncorrected_reflectivity_h' not in classification_radar.fields
    assert 'uncorrected_copol_correlation_coeff' not in classification_radar.fields
    assert resolved['z'] == 'uncorrected_reflectivity_h'
    assert resolved['rhohv'] == 'uncorrected_copol_correlation_coeff'
    assert np.ma.allequal(
        classification_radar.fields['reflectivity']['data'],
        radar.fields['uncorrected_reflectivity_h']['data'])

    assert set(moment_fields) == {
        'reflectivity', 'differential_reflectivity', 'cross_correlation_ratio',
        'normalized_coherent_power', 'signal_to_noise_ratio', 'spectral_width',
        'differential_phase', 'mean_doppler_velocity'}
    # Gate temperature is published for the classifier but is not evidence
    # that a gate was measured -- that distinction is the evidence guard.
    assert 'sounding_temperature' in classification_radar.fields
    assert 'sounding_temperature' not in moment_fields
    # The caller's volume is untouched.
    assert 'uncorrected_reflectivity_h' in radar.fields


def test_declined_volume_warns_rather_than_reading_as_clear_air():
    """A skipped sweep must not fold silently into no_scatter.

    radar_palette skips sweeps it judges unsuitable -- narrow-elevation-span
    RHIs in the TRACER cell-tracking sequence, for instance -- and returns
    unclassified for every gate in them.
    """
    from cmac.gate_id_backends import _report_unclassified

    codes = np.zeros((10, 20), dtype='i2')  # all unclassified
    meta = {'skipped_sweeps': [
        {'sweep': 0, 'sweep_mode': 'rhi', 'elevation_span': 18.76}]}
    with pytest.warns(UserWarning, match='unclassified'):
        n_unclassified, skipped = _report_unclassified(codes, 0, meta, {})
    assert n_unclassified == codes.size
    assert len(skipped) == 1

    with pytest.raises(RuntimeError, match='elevation span 18.8'):
        _report_unclassified(codes, 0, meta,
                             {'gate_id_unclassified_policy': 'error'})

    with pytest.raises(ValueError, match='must be'):
        _report_unclassified(codes, 0, meta,
                             {'gate_id_unclassified_policy': 'shrug'})


def test_classified_volume_does_not_warn():
    from cmac.gate_id_backends import _report_unclassified

    codes = np.full((10, 20), 5, dtype='i2')  # all light_rain
    codes[0, :] = 0
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        n_unclassified, skipped = _report_unclassified(codes, 0, {}, {})
    assert n_unclassified == 20
    assert skipped == []


def test_classification_radar_falls_back_to_the_config(radar):
    """Platforms with no uncorrected moment use the configured field.

    Legacy X-SAPR (MDV) and NEXRAD volumes publish none of the uncorrected
    names, so the per-radar field_names entry has to remain the fallback.
    """
    for name in ('uncorrected_reflectivity_h',
                 'uncorrected_copol_correlation_coeff'):
        del radar.fields[name]
    classification_radar, _, resolved = build_classification_radar(
        radar, FIELD_CONFIG)
    assert resolved['z'] == 'reflectivity'
    assert resolved['rhohv'] == 'copol_correlation_coeff'
    assert np.ma.allequal(
        classification_radar.fields['reflectivity']['data'],
        radar.fields['reflectivity']['data'])


def test_calibration_offsets_reach_the_uncorrected_moments(radar):
    """cmac() offsets the configured fields, so this view offsets its own."""
    cmac_config = {'ref_offset': 0.8, 'zdr_offset': 0.7}
    classification_radar, _, _ = build_classification_radar(
        radar, FIELD_CONFIG, cmac_config)
    assert np.ma.allclose(
        classification_radar.fields['reflectivity']['data'],
        radar.fields['uncorrected_reflectivity_h']['data'] + 0.8)
    assert np.ma.allclose(
        classification_radar.fields['differential_reflectivity']['data'],
        radar.fields['uncorrected_differential_reflectivity']['data'] + 0.7)
    # The volume being processed must not see the offset twice.
    assert np.ma.allequal(radar.fields['uncorrected_reflectivity_h']['data'],
                          np.ma.masked_invalid(
                              radar.fields['reflectivity']['data'] - 10.0))


def test_calibration_offsets_not_applied_to_a_config_fallback(radar):
    """A configured field has already been offset in place by cmac()."""
    del radar.fields['uncorrected_reflectivity_h']
    classification_radar, _, resolved = build_classification_radar(
        radar, FIELD_CONFIG, {'ref_offset': 0.8})
    assert resolved['z'] == 'reflectivity'
    assert np.ma.allequal(
        classification_radar.fields['reflectivity']['data'],
        radar.fields['reflectivity']['data'])


def test_calibration_offsets_can_be_switched_off(radar):
    classification_radar, _, _ = build_classification_radar(
        radar, FIELD_CONFIG,
        {'ref_offset': 0.8, 'gate_id_apply_offsets': False})
    assert np.ma.allequal(
        classification_radar.fields['reflectivity']['data'],
        radar.fields['uncorrected_reflectivity_h']['data'])


def test_classification_radar_masks_the_sounding_fill(radar):
    classification_radar, _, _ = build_classification_radar(radar, FIELD_CONFIG)
    temperature = classification_radar.fields['sounding_temperature']['data']
    assert np.ma.getmaskarray(temperature)[:, 0].all()
    assert not np.ma.getmaskarray(temperature)[:, 1:].any()
    # The radar handed in keeps its fill value; only the view is cleaned.
    assert (radar.fields['sounding_temperature']['data'][:, 0] == -9999.0).all()


def test_classification_radar_probes_for_spectrum_width(radar):
    """Spectrum width is found even though field_names has no key for it."""
    del radar.fields['uncorrected_spectral_width_h']
    radar.fields['spectrum_width'] = radar.fields.pop('spectral_width')
    classification_radar, moment_fields, resolved = build_classification_radar(
        radar, FIELD_CONFIG)
    assert 'spectral_width' in classification_radar.fields
    assert 'spectral_width' in moment_fields
    assert resolved['sw'] == 'spectrum_width'


def test_sounding_freezing_level_from_the_gate_profile(radar):
    freezing_level = sounding_freezing_level(radar)
    altitude = radar.gate_altitude['data']
    sub_freezing = altitude > radar.freezing_altitude
    assert freezing_level == pytest.approx(altitude[sub_freezing].min())


def test_sounding_freezing_level_is_none_without_cold_gates(radar):
    radar.fields['sounding_temperature']['data'][:] = 15.0
    assert sounding_freezing_level(radar) is None


def test_sounding_freezing_level_ignores_the_fill_value(radar):
    """-9999 is colder than any real gate; it must not become the answer."""
    radar.fields['sounding_temperature']['data'][:] = 15.0
    radar.fields['sounding_temperature']['data'][:, 0] = -9999.0
    assert sounding_freezing_level(radar) is None


def test_missing_radar_palette_gives_an_actionable_error(monkeypatch):
    """Selecting the backend without the package must explain the fix."""
    monkeypatch.setitem(sys.modules, 'radar_palette.gateid', None)
    with pytest.raises(ImportError, match="gate_id_method='cmac_fuzzy'"):
        _import_radar_palette()


@pytest.mark.skipif(not radar_palette_available(),
                    reason='radar_palette is not installed')
def test_evidence_guard_demotes_gates_with_no_measurement(radar):
    """A gate with no finite measured moment cannot carry a hydrometeor label.

    The classifier scores gate temperature and height over the freezing level,
    both of which are derived from gate geometry and finite everywhere, so
    without this guard an unmeasured gate scores above zero and is labelled.
    """
    from cmac.gate_id_backends import radar_palette_gate_id

    gid, categories, extra_fields, meta = radar_palette_gate_id(
        radar, FIELD_CONFIG, {})

    assert categories == CMAC_GATE_ID_CATEGORIES
    assert gid['notes'].startswith('0:multi_trip,1:rain,2:snow')

    detail = extra_fields['scatterer_classification']['data']
    no_scatter = 1  # radar_palette's own code for no_scatter
    assert (detail[:, 0] == no_scatter).all()
    assert gid['data'][:, 0].tolist() == [
        CMAC_GATE_ID_CATEGORIES.index('no_scatter')] * radar.nrays
    assert meta['n_no_evidence'] >= 0
    # Every published code must be describable by the notes string.
    assert gid['data'].max() < len(CMAC_GATE_ID_CATEGORIES)


@pytest.mark.skipif(not radar_palette_available(),
                    reason='radar_palette is not installed')
def test_detail_field_declares_its_flag_values(radar):
    from cmac.gate_id_backends import radar_palette_gate_id

    _, _, extra_fields, _ = radar_palette_gate_id(radar, FIELD_CONFIG, {})
    detail = extra_fields['scatterer_classification']
    assert detail['flag_values'] == sorted(RADAR_PALETTE_CLASSES)
    assert detail['flag_meanings'].split() == [
        RADAR_PALETTE_CLASSES[code] for code in sorted(RADAR_PALETTE_CLASSES)]
    # The margin field is opt-in, so it is absent by default.
    assert 'scatterer_classification_margin' not in extra_fields


@pytest.mark.skipif(not radar_palette_available(),
                    reason='radar_palette is not installed')
def test_margin_is_published_when_the_config_asks(radar):
    from cmac.gate_id_backends import radar_palette_gate_id

    _, _, extra_fields, _ = radar_palette_gate_id(
        radar, FIELD_CONFIG, {'gate_id_publish_margin': True})
    assert 'scatterer_classification_margin' in extra_fields
