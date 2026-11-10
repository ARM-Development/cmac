"""Tests for aligning PPI clutter maps with radar sweeps."""

import numpy as np

from cmac import add_clutter_map


class _Radar:
    def __init__(self, fixed_angle, azimuth, clutter=None):
        self.scan_type = 'ppi'
        self.nrays = len(azimuth)
        self.ngates = 2
        self.nsweeps = len(fixed_angle)
        self.fixed_angle = {'data': np.asarray(fixed_angle)}
        self.azimuth = {'data': np.asarray(azimuth)}
        self.sweep_start_ray_index = {
            'data': np.arange(self.nsweeps, dtype=int) * 2}
        self.sweep_end_ray_index = {
            'data': np.arange(1, self.nrays, 2, dtype=int)}
        self.fields = {} if clutter is None else {
            'ground_clutter': {'data': np.asarray(clutter)}}

    def get_start_end(self, sweep):
        return (self.sweep_start_ray_index['data'][sweep],
                self.sweep_end_ray_index['data'][sweep])

    def add_field(self, name, field, replace_existing=False):
        self.fields[name] = field


def test_ppi_clutter_map_matches_sweeps_by_elevation_and_azimuth():
    radar = _Radar([1.0, 2.0], [0.0, 180.0, 0.0, 180.0])
    clutter = _Radar([1.0], [1.0, 181.0], [[1, 0], [0, 1]])

    add_clutter_map(radar, clutter)

    np.testing.assert_array_equal(
        radar.fields['ground_clutter']['data'],
        [[1, 0], [0, 1], [0, 0], [0, 0]])

