"""Tests for the masks carried by paired phase fields."""

import numpy as np

from cmac.cmac_processing import synchronize_phase_field_masks


def test_synchronize_phase_field_masks_uses_union_of_masks():
    phidp = {'data': np.ma.array([[1.0, 2.0, 3.0]], mask=[[0, 1, 0]])}
    kdp = {'data': np.ma.array([[4.0, 5.0, 6.0]], mask=[[0, 0, 1]])}

    synchronize_phase_field_masks(phidp, kdp)

    expected = np.array([[False, True, True]])
    np.testing.assert_array_equal(np.ma.getmaskarray(phidp['data']), expected)
    np.testing.assert_array_equal(np.ma.getmaskarray(kdp['data']), expected)

