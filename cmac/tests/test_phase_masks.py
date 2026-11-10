"""Tests for the masks carried by paired phase fields."""

from types import SimpleNamespace

import numpy as np

from cmac.cmac_processing import fix_phase_fields, synchronize_phase_field_masks
from cmac.cmac_radar import _get_field_fill_value


def test_synchronize_phase_field_masks_uses_union_of_masks():
    phidp = {'data': np.ma.array([[1.0, 2.0, 3.0]], mask=[[0, 1, 0]])}
    kdp = {'data': np.ma.array([[4.0, 5.0, 6.0]], mask=[[0, 0, 1]])}

    synchronize_phase_field_masks(phidp, kdp)

    expected = np.array([[False, True, True]])
    np.testing.assert_array_equal(np.ma.getmaskarray(phidp['data']), expected)
    np.testing.assert_array_equal(np.ma.getmaskarray(kdp['data']), expected)


def test_fix_phase_fields_does_not_integrate_fill_values():
    kdp = {'data': np.ma.array([[1.0, -9999.0, 2.0]], mask=[[0, 1, 0]])}
    phidp = {'data': np.ma.array([[0.0, 0.0, 0.0]], mask=[[0, 0, 0]])}
    gates = SimpleNamespace(gate_excluded=np.array([[False, False, True]]))

    filtered_phase, filtered_kdp = fix_phase_fields(
        kdp, phidp, np.array([0.0, 1.0, 2.0]), gates)

    assert np.ma.getdata(filtered_phase['data']).max() < 10.0
    assert np.ma.getdata(filtered_kdp['data']).max() < 10.0
    np.testing.assert_array_equal(
        np.ma.getmaskarray(filtered_phase['data']),
        [[False, True, True]])
    np.testing.assert_array_equal(
        np.ma.getmaskarray(filtered_kdp['data']),
        [[False, True, True]])


def test_get_field_fill_value_prefers_missing_value():
    assert _get_field_fill_value({
        'missing_value': -9999,
        '_FillValue': -32767,
    }) == -9999.0
    assert _get_field_fill_value({'_FillValue': -32767}) == -32767.0

