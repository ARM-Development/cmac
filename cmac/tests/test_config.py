""" Unit Tests for CMAC's config.py module. """

import os
import textwrap

import pytest

from cmac.config import (get_cmac_values, get_field_names,
                         get_plot_values, get_metadata,
                         get_zs_relationships, get_default_metadata)


def test_get_cmac_values():
    cmac_config = get_cmac_values('xsapr_i5_ppi')
    assert type(cmac_config) == dict

    assert cmac_config['save_name'] == 'sgpxsaprcmacsecI5.c1'
    assert cmac_config['site_alt'] == 328
    assert cmac_config['ref_offset'] == 0.0
    assert cmac_config['self_const'] == 60000.00
    assert cmac_config['attenuation_a_coef'] == 0.17

def test_get_field_names():
    field_config = get_field_names('xsapr_i5_ppi')
    assert type(field_config) == dict

    assert field_config['reflectivity'] == 'reflectivity'
    assert field_config['temperature'] == 'tdry'


def test_get_metadata():
    meta_config = get_metadata('xsapr_i5_ppi')
    assert type(meta_config) == dict

    assert meta_config['site_id'] == 'sgp'
    assert meta_config['facility_id'] == 'I5: Garber, OK'
    assert meta_config['version'] == '2.0 lite'


def test_get_plot_values():
    plot_config = get_plot_values('xsapr_i5_ppi')
    assert type(plot_config) == dict

    assert plot_config['sweep'] == 3
    assert plot_config['max_lat'] == 37.0
    assert plot_config['min_lon'] == -98.3
    assert plot_config['site_i5_dms_lat'] == (36, 29, 29.4)
    assert plot_config['site_i5_dms_lon'] == (-97, 35, 37.68)


# -- YAML overrides ---------------------------------------------------------

YAML_BODY = textwrap.dedent("""
    cmac_values:
      xsapr_i5_ppi:
        ref_offset: 1.25
        zdr_offset: 2.5
      my_new_radar:
        save_name: my_radar.c1
        site_alt: 500
        ref_offset: 0.5
    metadata:
      xsapr_i5_ppi:
        developers: "Override Author"
    field_names:
      xsapr_i5_ppi:
        reflectivity: my_reflectivity
    plot_values:
      xsapr_i5_ppi:
        sweep: 7
    zs_relationships:
      My Test Relationship:
        A: 99
        B: 1.5
        abbreviation: mytest
    """)


@pytest.fixture
def yaml_config(tmp_path):
    path = tmp_path / "user_config.yaml"
    path.write_text(YAML_BODY)
    return str(path)


def test_yaml_overrides_cmac_values(yaml_config):
    cfg = get_cmac_values('xsapr_i5_ppi', config_file=yaml_config)
    # Overridden values come from YAML.
    assert cfg['ref_offset'] == 1.25
    assert cfg['zdr_offset'] == 2.5
    # Untouched values still come from the defaults.
    assert cfg['save_name'] == 'sgpxsaprcmacsecI5.c1'
    assert cfg['site_alt'] == 328


def test_yaml_overrides_metadata(yaml_config):
    meta = get_metadata('xsapr_i5_ppi', config_file=yaml_config)
    assert meta['developers'] == 'Override Author'
    # Fallback for un-overridden keys.
    assert meta['site_id'] == 'sgp'


def test_yaml_overrides_field_names(yaml_config):
    fields = get_field_names('xsapr_i5_ppi', config_file=yaml_config)
    assert fields['reflectivity'] == 'my_reflectivity'
    assert fields['temperature'] == 'tdry'


def test_yaml_overrides_plot_values(yaml_config):
    plot = get_plot_values('xsapr_i5_ppi', config_file=yaml_config)
    assert plot['sweep'] == 7
    assert plot['min_lon'] == -98.3


def test_yaml_adds_new_radar(yaml_config):
    cfg = get_cmac_values('my_new_radar', config_file=yaml_config)
    assert cfg['save_name'] == 'my_radar.c1'
    assert cfg['site_alt'] == 500
    assert cfg['ref_offset'] == 0.5


def test_yaml_adds_zs_relationship(yaml_config):
    rels = get_zs_relationships(config_file=yaml_config)
    assert 'My Test Relationship' in rels
    assert rels['My Test Relationship']['A'] == 99
    # Defaults still present.
    assert 'Wolf and Snider (2012)' in rels


def test_yaml_does_not_mutate_defaults(yaml_config):
    # Mutate the dict returned via YAML and confirm defaults stay clean.
    cfg = get_cmac_values('xsapr_i5_ppi', config_file=yaml_config)
    cfg['ref_offset'] = 999
    default_cfg = get_cmac_values('xsapr_i5_ppi')
    assert default_cfg['ref_offset'] == 0.0


def test_yaml_missing_file_raises(tmp_path):
    missing = str(tmp_path / "nope.yaml")
    with pytest.raises(FileNotFoundError):
        get_cmac_values('xsapr_i5_ppi', config_file=missing)


# -- New soft-coded parameter defaults -------------------------------------


def test_processing_defaults_present_for_all_radars():
    """Every radar gains the processing tunables from default_config."""
    for radar in ('xsapr_i5_ppi', 'cacti_csapr2_ppi', 'bnf_csapr2_ppi',
                  'sail_xband_ppi', 'nsa_xsapr_ppi', 'tracer_csapr2_ppi'):
        cfg = get_cmac_values(radar)
        assert cfg['snow_density'] == 0.073
        assert cfg['phidp_nowrap'] == 50
        assert cfg['bringi_nfilter'] == 1
        assert cfg['bringi_window'] == 3.0
        assert cfg['phidp_despeckle_size'] == 49
        assert cfg['melt_fzl_ceiling'] == 5000.0
        assert cfg['melt_fzl_replacement'] == 3500.0
        assert cfg['melt_fzl_floor'] == 1000.0
        assert cfg['velocity_texture_window'] == 4
        assert cfg['area_coverage_precip_threshold'] == 10.0
        assert cfg['area_coverage_convection_threshold'] == 40.0
        assert cfg['cbb_blockage_threshold'] == 0.80


def test_plot_defaults_present_for_all_radars():
    """Every radar gains the plot tunables from default_config."""
    for radar in ('xsapr_i5_ppi', 'cacti_csapr2_ppi', 'bnf_csapr2_ppi',
                  'sail_xband_ppi', 'nsa_xsapr_ppi', 'tracer_csapr2_ppi'):
        cfg = get_plot_values(radar)
        assert cfg['reflectivity_vmin'] == -8
        assert cfg['reflectivity_vmax'] == 40
        assert cfg['corrected_velocity_vmin'] == -60
        assert cfg['corrected_velocity_vmax'] == 60
        assert cfg['rain_rate_vmin'] == 0
        assert cfg['rain_rate_vmax'] == 120
        assert cfg['figsize_single'] == [12, 8]
        assert cfg['figsize_panel'] == [15, 10]
        assert cfg['sweep_fallback_nsweeps_lt'] == 4
        assert cfg['sweep_fallback'] == 2
        assert cfg['cat_colors']['rain'] == 'green'
        assert cfg['cat_colors']['clutter'] == 'black'


PROCESSING_OVERRIDE_YAML = textwrap.dedent("""
    cmac_values:
      xsapr_i5_ppi:
        snow_density: 0.10
        phidp_nowrap: 80
        bringi_nfilter: 2
        bringi_window: 6.0
        melt_fzl_ceiling: 6000.0
        area_coverage_precip_threshold: 5.0
        cbb_blockage_threshold: 0.6
    plot_values:
      xsapr_i5_ppi:
        reflectivity_vmax: 55
        corrected_velocity_vmin: -45
        figsize_single: [10, 6]
        ymax: 12
        cat_colors:
          rain: blue
          snow: white
          multi_trip: red
          no_scatter: gray
          melting: yellow
          clutter: black
    default_metadata:
      developers: "Override Author"
      institution: "Test Institution"
    """)


@pytest.fixture
def processing_override_config(tmp_path):
    path = tmp_path / "processing_overrides.yaml"
    path.write_text(PROCESSING_OVERRIDE_YAML)
    return str(path)


def test_yaml_overrides_processing_tunables(processing_override_config):
    cfg = get_cmac_values('xsapr_i5_ppi', config_file=processing_override_config)
    assert cfg['snow_density'] == 0.10
    assert cfg['phidp_nowrap'] == 80
    assert cfg['bringi_nfilter'] == 2
    assert cfg['bringi_window'] == 6.0
    assert cfg['melt_fzl_ceiling'] == 6000.0
    assert cfg['area_coverage_precip_threshold'] == 5.0
    assert cfg['cbb_blockage_threshold'] == 0.6
    # Defaults still surface for keys not overridden.
    assert cfg['phidp_despeckle_size'] == 49


def test_yaml_overrides_plot_ranges(processing_override_config):
    cfg = get_plot_values('xsapr_i5_ppi', config_file=processing_override_config)
    assert cfg['reflectivity_vmax'] == 55
    assert cfg['corrected_velocity_vmin'] == -45
    assert cfg['figsize_single'] == [10, 6]
    assert cfg['ymax'] == 12
    assert cfg['cat_colors']['rain'] == 'blue'
    # Defaults preserved when not overridden.
    assert cfg['rain_rate_vmax'] == 120


def test_get_default_metadata_returns_builtin_fallback():
    meta = get_default_metadata()
    assert meta['vap_name'] == 'cmac'
    assert meta['version'] == '2.0 lite'
    assert meta['Conventions'] == 'CF/Radial instrument_parameters ARM-1.3'


def test_get_default_metadata_yaml_override(processing_override_config):
    meta = get_default_metadata(config_file=processing_override_config)
    assert meta['developers'] == 'Override Author'
    assert meta['institution'] == 'Test Institution'
    # Untouched keys keep their built-in defaults.
    assert meta['vap_name'] == 'cmac'
