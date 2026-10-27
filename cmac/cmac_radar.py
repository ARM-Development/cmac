""" Module that uses CMAC to remove and correct second trip returns,
correct velocity and more. A new radar object is then created with all CMAC
2.0 products. """

import copy
import json
import sys
import warnings

import xarray as xr
import numpy as np
import pyart
import netCDF4

from .cmac_processing import (
    do_my_fuzz, get_melt, get_texture, fix_phase_fields, gen_clutter_field_from_refl, beam_block,
    snow_rate, rain_rate, get_sys_phase, remove_sys_phase)
from .config import (get_cmac_values, get_field_names, get_metadata,
                     get_zs_relationships, get_default_metadata)
from .gate_id import append_gate_id_category, get_gate_id_categories
from .gate_id_backends import radar_palette_gate_id
from . import csu_kdp

def cmac(radar, sonde, config, geotiff=None, flip_velocity=False,
         meta_append=None, verbose=True, snow_density=None, snowfall=True,
         config_file=None):
    """
    Corrected Moments in Antenna Coordinates

    Parameters
    ----------
    radar : Radar
        Radar object to use in the CMAC calculation.
    sonde : xarray Dataset
        Object containing all the sonde data.
    config : str
        A string pointing to dictionaries containing values for CMAC
        specific to a radar.

    Other Parameters
    ----------------
    geotiff : str
        Filepath for a geotiff, if provided, will generate a beam blockage
        gate id.
    meta_append : dict, json and None
        Value key pairs to attend to global attributes. If None,
        a default metadata will be created. The metadata can also
        be created by providing a dictionary or a json file.
    verbose : bool
        If True, this will display more statistics.
    snow_density : float or None
        1 / Snow water equivalent ratio for snowfall rate. If None, the
        value is taken from the ``snow_density`` key of the radar config
        (default ``0.073``).
    config_file : str or None
        Path to a YAML file whose values override the built-in defaults for
        the named ``config`` radar. See ``cmac.config`` for the expected
        layout. When None, only the built-in defaults are used.

    Returns
    -------
    radar : Radar
        Radar object with new CMAC added fields.
    """
    # Retrieve values from the configuration file.
    cmac_config = get_cmac_values(config, config_file=config_file)
    field_config = get_field_names(config, config_file=config_file)
    meta_config = get_metadata(config, config_file=config_file)
    zs_relationship_dict = get_zs_relationships(config_file=config_file)

    if snow_density is None:
        snow_density = cmac_config.get('snow_density', 0.073)
    # Over write site altitude

    if 'site_alt' in cmac_config.keys():
        radar.altitude['data'][0] = cmac_config['site_alt']

    # Obtaining variables needed for fuzzy logic.

    ##radar_start_date = netCDF4.num2date(
    ##    radar.time['data'][0], radar.time['units'],
    ##    only_use_cftime_datetimes=False, only_use_python_datetimes=True)
    ##print('##', str(radar_start_date))

    temp_field = field_config['temperature']
    alt_field = field_config['altitude']
    vel_field = field_config['velocity']

    if 'gen_clutter_from_refl' not in cmac_config.keys():
        cmac_config['gen_clutter_from_refl'] = False

    if cmac_config['gen_clutter_from_refl']:
        new_clutter_field = gen_clutter_field_from_refl(
            radar, field_config['input_clutter_corrected_reflectivity'],
            field_config['reflectivity'],
            diff_dbz=cmac_config['gen_clutter_from_refl_diff'],
            max_h=cmac_config['gen_clutter_from_refl_alt'])
        radar.add_field(
            field_config['clutter'], new_clutter_field, replace_existing=True)

    # ZDR offsets
    if 'zdr_offset' in cmac_config.keys():
        if 'offset_zdrs' in cmac_config.keys():
            for fld in cmac_config['offset_zdrs']:
                radar.fields[fld]['data'] += cmac_config['zdr_offset']
        else:
            radar.fields[
                field_config['input_zdr']]['data'] += cmac_config['zdr_offset']
    
    # Reflectivity offsets
    if cmac_config["ref_offset"]:
        # note need input reflectivity, not corrected reflectivity variable name
        radar.fields[field_config["reflectivity"]]['data'] += cmac_config["ref_offset"]
        
    # flipping phidp
    if 'flip_phidp' not in cmac_config.keys():
        cmac_config['flip_phidp'] = False

    if cmac_config['flip_phidp']:
        # user specifies fields to flip
        if 'phidp_flipped' in cmac_config.keys():
            for fld in cmac_config['phidp_flipped']:
                radar.fields[fld]['data'] = radar.fields[fld]['data'] * -1.0
        else:  # just flip defined phidp field
            radar.fields[
                field_config['input_phidp_field']]['data'] = radar.fields[
                    field_config['input_phidp_field']]['data']*-1.0

    if flip_velocity:
        radar.fields[vel_field]['data'] = radar.fields[
            vel_field]['data'] * -1.0

    z_dict, temp_dict = pyart.retrieve.map_profile_to_gates(
        sonde.variables[temp_field][:], sonde.variables[alt_field][:], radar)

    if 'clutter_mask_z_for_texture' not in cmac_config.keys():
        cmac_config['clutter_mask_z_for_texture'] = False

    if cmac_config['clutter_mask_z_for_texture']:
        masked_vr = copy.deepcopy(radar.fields[vel_field])
        if 'ground_clutter' in radar.fields.keys():
            masked_vr['data'] = np.ma.masked_where(
                radar.fields['ground_clutter']['data'] == 1, masked_vr['data'])
            masked_vr[
                'data'][radar.fields['ground_clutter']['data'] == 1] = np.nan
        radar.add_field(
            'clutter_masked_velocity', masked_vr, replace_existing=True)
        radar.fields[
            'clutter_masked_velocity']['long_name'] = 'Radial mean Doppler velocity, positive for motion away from the instrument, clutter removed'

        texture = get_texture(
            radar, 'clutter_masked_velocity',
            window=cmac_config.get('velocity_texture_window', 4),
            median_size=cmac_config.get('velocity_texture_median_size', (4, 4)))
        texture['data'][np.isnan(texture['data'])] = 0.0
    else:
        texture = get_texture(
            radar, vel_field,
            window=cmac_config.get('velocity_texture_window', 4),
            median_size=cmac_config.get('velocity_texture_median_size', (4, 4)))
    
    if field_config['signal_to_noise_ratio'] is None:
        snr = pyart.retrieve.calculate_snr_from_reflectivity(radar)

    if not verbose:
        print('## Adding radar fields...')

    if verbose:
        print('##')
        print('## These radar fields are being added:')
    temp_dict['units'] = 'degC'
    z_dict['units'] = 'm'
    temp_dict["data"] = temp_dict["data"].filled(-9999)
    radar.add_field('sounding_temperature', temp_dict, replace_existing=True)
    radar.add_field('height', z_dict, replace_existing=True)
    

    if field_config['signal_to_noise_ratio'] is None:
        radar.add_field('signal_to_noise_ratio', snr, replace_existing=True)
    else:
        radar.fields[
            'signal_to_noise_ratio'] = radar.fields[
                field_config['signal_to_noise_ratio']].copy()
    radar.add_field('velocity_texture', texture, replace_existing=True)
    if verbose:
        print('##    sounding_temperature')
        print('##    height')
        print('##    signal_to_noise_ratio')
        print('##    velocity_texture')

    # Performing fuzzy logic to obtain the gate ids.
    rhv_field = field_config['cross_correlation_ratio']
    ncp_field = field_config['normalized_coherent_power']

    if 'mbfs' not in cmac_config:
        cmac_config['mbfs'] = None

    if 'hard_const' not in cmac_config:
        cmac_config['hard_const'] = None

    if 'kdp_method' not in cmac_config:
        cmac_config['kdp_method'] = 'lp'

    # Specifically for dealing with the ingested C-SAPR2 data

    # Which classifier fills gate_id is a per-radar configuration choice. Both
    # backends publish the same five categories in the same order, documented
    # in the field's notes attribute, because everything below this point --
    # the dealiasing gates, the KDP and attenuation gates, and all three
    # rain-rate estimators -- reads its gate selection from that one field.
    gate_id_method = cmac_config.get('gate_id_method', 'cmac_fuzzy')
    gate_id_meta = None
    if gate_id_method == 'cmac_fuzzy':
        my_fuzz, _ = do_my_fuzz(
            radar, rhv_field, ncp_field, verbose=verbose,
            tex_start=cmac_config.get('fuzzy_tex_start', 2.0),
            tex_end=cmac_config.get('fuzzy_tex_end', 2.1),
            custom_mbfs=cmac_config['mbfs'],
            custom_hard_constraints=cmac_config['hard_const'],
            median_size=cmac_config.get('fuzzy_score_median_size', (3, 4)))

        radar.add_field('gate_id', my_fuzz,
                        replace_existing=True)
    elif gate_id_method == 'radar_palette':
        gid, _categories, extra_fields, gate_id_meta = radar_palette_gate_id(
            radar, field_config, cmac_config, verbose=verbose)
        radar.add_field('gate_id', gid, replace_existing=True)
        # The eleven-class classification, and optionally its score margin,
        # travel alongside the folded field rather than replacing it.
        for field_name, field_dict in extra_fields.items():
            radar.add_field(field_name, field_dict, replace_existing=True)
        if verbose:
            for field_name in extra_fields:
                print('##    %s' % field_name)
    else:
        raise ValueError(
            "Unknown gate_id_method %r in the configuration for %r. Valid "
            "choices are 'cmac_fuzzy' (CMAC's own fuzzy classifier) and "
            "'radar_palette'." % (gate_id_method, config))

    # The clutter and terrain-blockage categories are appended through
    # append_gate_id_category, which is idempotent and returns the code to
    # write. A volume carrying both a ground_clutter field and a vendor
    # classification_mask used to get ',5:clutter' appended once for each,
    # and because get_gate_id_categories reads a category's code from its
    # position in the notes string, clutter then resolved to 6 while the
    # gates had been set to 5.
    if 'ground_clutter' in radar.fields.keys():
        clutter_data = radar.fields['ground_clutter']['data']
        clutter_code = append_gate_id_category(
            radar.fields['gate_id'], 'clutter')
        radar.fields['gate_id']['data'][clutter_data == 1] = clutter_code

    # The vendor classification_mask overlay is opt-out per radar because its
    # semantics are not the same across instrument generations. On TRACER
    # C-SAPR2 a1 volumes the mask equals 8 -- its 'clutter' bit, and nothing
    # else -- at 171,560 of 171,600 gates, so this block relabels effectively
    # the whole volume as clutter and no meteorological gate survives. ARM's
    # own production CMAC output for the same volume carries no clutter code
    # at all, so the overlay was not applied to that generation of data. On
    # CACTI C-SAPR2 the same field is 0 over 94% of gates and the overlay
    # behaves as intended, so the default stays on.
    use_classification_mask = cmac_config.get('use_classification_mask', True)
    if 'classification_mask' in radar.fields.keys() and use_classification_mask:
        clutter_data = radar.fields['classification_mask']['data']
        gate_data = radar.fields['gate_id']['data'].copy()
        clutter_code = append_gate_id_category(
            radar.fields['gate_id'], 'clutter')
        radar.fields['gate_id']['data'][clutter_data == 8] = clutter_code
        radar.fields['gate_id']['data'][clutter_data == 16] = clutter_code
        radar.fields['gate_id']['data'][clutter_data == 4] = clutter_code
        radar.fields['gate_id']['data'][clutter_data == 1] = 0
        radar.fields['gate_id']['data'][clutter_data == 2] = 0
        radar.fields['gate_id']['data'][gate_data == 0] = 0

    cbb_threshold = cmac_config.get('cbb_blockage_threshold', 0.80)
    if geotiff is not None:
        pbb_all, cbb_all = beam_block(
            radar, geotiff, cmac_config['radar_height_offset'],
            cmac_config['beam_width'])
        blockage_code = append_gate_id_category(
            radar.fields['gate_id'], 'terrain_blockage')
        radar.fields['gate_id']['data'][
            cbb_all > cbb_threshold] = blockage_code

        pbb_dict = pbb_to_dict(pbb_all)
        cbb_dict = cbb_to_dict(cbb_all)
        radar.add_field('partial_beam_blockage', pbb_dict)
        radar.add_field('cumulative_beam_blockage', cbb_dict)

    if 'cbb_flag' in radar.fields.keys():
        cbb = radar.fields['cbb_flag']['data']
        if cbb.shape[0] < radar.fields['gate_id']['data'].shape[0]:
            # find the difference in shape
            sdiff = radar.fields['gate_id']['data'].shape[0] - cbb.shape[0]
            # pad the cbb gate to match the radar
            cbb = np.pad(cbb, ((0, sdiff), (0, 0)),  'maximum')
        blockage_code = append_gate_id_category(
            radar.fields['gate_id'], 'terrain_blockage')
        radar.fields['gate_id']['data'][cbb == 1] = blockage_code

    cat_dict = {}
    for pair_str in radar.fields['gate_id']['notes'].split(','):
        cat_dict.update(
            {pair_str.split(':')[1]:int(pair_str.split(':')[0])})

    if verbose:
        print('##    gate_id')

    # Corrected velocity using pyart's region dealiaser.
    cmac_gates = pyart.correct.GateFilter(radar)
    cmac_gates.exclude_all()
    cmac_gates.include_equal('gate_id', cat_dict['rain'])
    cmac_gates.include_equal('gate_id', cat_dict['melting'])
    cmac_gates.include_equal('gate_id', cat_dict['snow'])
    
    # Create a simulated velocity field from the sonde object.
    u_field = field_config['u_wind']
    v_field = field_config['v_wind']
    u_wind = sonde[u_field].values
    v_wind = sonde[v_field].values
    alt_field = field_config['altitude']
    sonde_alt = sonde[alt_field].values
    profile = pyart.core.HorizontalWindProfile.from_u_and_v(
        sonde_alt, u_wind, v_wind)
    sim_vel = pyart.util.simulated_vel_from_profile(radar, profile)
    radar.add_field('simulated_velocity', sim_vel, replace_existing=True)

    # Create the corrected velocity field from the region dealias algorithm.
    speckled_cmac_gates = pyart.correct.despeckle_field(
        radar, vel_field, gatefilter=cmac_gates)
    if radar.scan_type == "rhi":
        corr_vel = pyart.correct.dealias_region_based(
            radar, vel_field=vel_field,
            keep_original=False, gatefilter=speckled_cmac_gates, centered=True)
    else:
        corr_vel = pyart.correct.dealias_region_based(
            radar, vel_field=vel_field, ref_vel_field='simulated_velocity',
            keep_original=False, gatefilter=speckled_cmac_gates, centered=True)

    radar.add_field('corrected_velocity', corr_vel, replace_existing=True)
    if verbose:
        print('##    corrected_velocity')
        print('##    simulated_velocity')

    fzl = get_melt(
        radar,
        fzl_ceiling=cmac_config.get('melt_fzl_ceiling', 5000.0),
        fzl_replacement=cmac_config.get('melt_fzl_replacement', 3500.0),
        fzl_floor=cmac_config.get('melt_fzl_floor', 1000.0))

    # Is the freezing level realistic? If not, assume

    ref_offset = cmac_config['ref_offset']
    self_const = cmac_config['self_const']
    phidp_nowrap = cmac_config.get('phidp_nowrap', 50)
    # Calculating differential phase fields.
    radar.fields[field_config['input_phidp_field']]['data'][
        radar.fields[field_config['input_phidp_field']]['data'] < 0] += 360.0
    if not "unfolded_differential_phase" in radar.fields.keys():
        radar.fields["unfolded_differential_phase"] = copy.deepcopy(
                radar.fields[field_config['input_phidp_field']])

    kdp_gates = copy.deepcopy(cmac_gates)
    kdp_gates.exclude_above('height', fzl)
    if cmac_config['kdp_method'] == 'lp':
        phidp, kdp = pyart.correct.phase_proc_lp_gf(
            radar, gatefilter=kdp_gates, offset=ref_offset, debug=True,
            LP_solver='cylp', nowrap=phidp_nowrap, fzl=fzl, self_const=self_const,
            phidp_field=field_config['input_phidp_field'],
            refl_field=field_config['reflectivity'])
    elif cmac_config['kdp_method'] == 'bringi':
        fill_value = -9999.
        dp = radar.fields[field_config['input_phidp_field']]['data']
        dz = radar.fields[field_config['reflectivity']]['data'] 
        # calc_kdp_bringi assumes PhiDP has the system phase offset removed
        # and is already unfolded. Feeding it the raw phase carries the
        # offset (~220 degrees at BNF) through to the Z-PHI attenuation,
        # where it is read as propagation phase and inflates the specific
        # attenuation by one to two orders of magnitude.
        sys_phase = cmac_config.get('phidp_sys_phase', None)
        if sys_phase is None:
            sys_phase = get_sys_phase(
                radar, gatefilter=kdp_gates,
                phidp_field=field_config['input_phidp_field'],
                ncp_field=field_config['normalized_coherent_power'],
                rhv_field=field_config['cross_correlation_ratio'])
        if sys_phase is None:
            warnings.warn(
                'Unable to estimate the PhiDP system phase offset; the raw '
                'phase will be processed unchanged. Set phidp_sys_phase in '
                'the configuration to supply it manually.', UserWarning)
        else:
            dp = remove_sys_phase(dp, sys_phase)
            if verbose:
                print('##    PhiDP system phase offset removed: '
                      '%.2f degrees' % sys_phase)
        dp = dp.filled(fill_value)
        dz = dz.filled(fill_value)
        rng = np.tile(radar.range['data'], (radar.nrays, 1)) / 1e3
        kdp, phidp, _ = csu_kdp.calc_kdp_bringi(dp=dp, dz=dz, rng=rng,
            bad=fill_value)
            
        kdp_data = np.ma.masked_where(
                kdp_gates.gate_excluded, kdp).filled(-9999.)
        phidp_data = np.ma.masked_where(kdp_gates.gate_excluded, phidp).filled(-9999.)
        phidp = copy.deepcopy(radar.fields[field_config['input_phidp_field']])
        kdp = pyart.config.get_metadata("corrected_specific_differential_phase")
        phidp["data"] = phidp_data
        kdp["data"] = kdp_data
        if sys_phase is not None:
            phidp["system_phase_offset"] = np.round(sys_phase, 4)
        

    print("Processed phase")
    # We do not use KDP, phase above freezing level
    kdp_gates = copy.deepcopy(cmac_gates)
    kdp_gates.exclude_above('height', fzl)
    
    radar.add_field('corrected_differential_phase', phidp,
                    replace_existing=True)
    radar.add_field('corrected_specific_diff_phase', kdp,
                    replace_existing=True)
    radar.fields[
        'corrected_differential_phase']['long_name'] = 'Corrected differential propagation phase shift'
   
    phidp_filt, kdp_filt = fix_phase_fields(
        copy.deepcopy(kdp), copy.deepcopy(phidp), radar.range['data'],
        kdp_gates, max_kdp=cmac_config.get('max_kdp', 15.0))
    
    radar.add_field('filtered_corrected_differential_phase', phidp,
                    replace_existing=True)
    radar.fields[
        'filtered_corrected_differential_phase']['long_name'] = 'Filtered corrected differential propagation phase shift'
    radar.add_field('filtered_corrected_specific_diff_phase', kdp_filt,
                    replace_existing=True)
    radar.fields[
        'filtered_corrected_specific_diff_phase']['long_name'] = 'Filtered Corrected Specific differential phase (KDP)'
    radar.fields['filtered_corrected_differential_phase']['long_name'] = 'Filtered Corrected Differential Phase'
    if verbose:
        print('##    corrected_specific_diff_phase')
        print('##    filtered_corrected_specific_diff_phase')
        print('##    corrected_differential_phase')
        print('##    filtered_corrected_differential_phase')

    # Calculating attenuation by using pyart.
    refl_field = field_config['reflectivity']
    attenuation_a_coef = cmac_config['attenuation_a_coef']
    c_coef = cmac_config['c_coef']
    d_coef = cmac_config['d_coef']
    beta_coef = cmac_config['beta_coef']
    zdr_field = field_config['differential_reflectivity']

    radar.fields['corrected_differential_reflectivity'] = copy.deepcopy(
        radar.fields[zdr_field])
    radar.fields['corrected_reflectivity'] = copy.deepcopy(
        radar.fields[refl_field])
    radar.fields['corrected_reflectivity']['data'] = np.ma.masked_where(
        cmac_gates.gate_excluded,
        radar.fields['corrected_reflectivity']['data'])

    # Get specific differential attenuation.
    # Need height over 0 degree isotherm
    iso0 = np.ma.mean(radar.fields['height']['data'][
        np.ma.where(np.abs(radar.fields['sounding_temperature']['data']) < 0.5)])
    radar.fields['height_over_iso0'] = copy.deepcopy(radar.fields['height'])
    radar.fields['height_over_iso0']['data'] -= iso0
    radar.fields['height_over_iso0']['long_name'] = 'Height of radar beam over freezing level'
    
    # Gates the Z-PHI attenuation correction is allowed to work on. The
    # melting layer is a valid radar return and belongs in the corrected
    # reflectivity, so it is included alongside rain and snow -- previously
    # this filter admitted gate_id 1 and 2 as bare literals, which excluded
    # melting and also assumed the fuzzy classifier's category order. The
    # codes now come from the field's own notes string, so either backend's
    # category list resolves correctly.
    phase_proc_categories = get_gate_id_categories(radar.fields['gate_id'])
    phase_proc_gates = pyart.filters.GateFilter(radar)
    phase_proc_gates.exclude_all()
    for category in ('rain', 'melting', 'snow'):
        code = phase_proc_categories.get(category)
        if code is not None:
            phase_proc_gates.include_equal('gate_id', code)
    phase_proc_gates.exclude_above(
        'corrected_specific_diff_phase',
        cmac_config.get('kdp_phase_proc_max', 10.0))
    phase_proc_gates = pyart.correct.despeckle_field(
        radar, 'differential_phase',
        gatefilter=phase_proc_gates,
        size=cmac_config.get('phidp_despeckle_size', 49))
    # calculate_attenuation_zphi defaults to temp_ref='temperature', which
    # ignores iso0_field altogether. Ask for the iso0 reference explicitly so
    # that the height_over_iso0 field built above is what sets the melting
    # layer, and fall back to the gate sounding temperature if the 0 degC
    # level could not be located.
    if np.isfinite(np.ma.filled(iso0, np.nan)):
        temp_ref = 'height_over_iso0'
        temp_field = None
    else:
        warnings.warn(
            'Could not locate the 0 degC level in the sounding; falling back '
            'to the gate sounding temperature to set the melting layer.',
            UserWarning)
        temp_ref = 'temperature'
        temp_field = 'sounding_temperature'
    (spec_at, pia_dict, cor_z, spec_diff_at,
     pida_dict, cor_zdr) = pyart.correct.calculate_attenuation_zphi(
         radar, temp_field=temp_field,
         zdr_field=field_config['zdr_field'],
         pia_field=field_config['pia_field'],
         iso0_field='height_over_iso0',
         phidp_field=field_config['phidp_field'],
         refl_field=field_config['refl_field'], c=c_coef, d=d_coef,
         a_coef=attenuation_a_coef, beta=beta_coef,
         gatefilter=phase_proc_gates, temp_ref=temp_ref)
    #  cor_zdr['data'] += cmac_config['zdr_offset'] Now taken care of at start
    radar.add_field('specific_attenuation', spec_at, replace_existing=True)
    radar.add_field('path_integrated_attenuation', pia_dict,
                    replace_existing=True)
    radar.add_field('corrected_reflectivity', cor_z, replace_existing=True)
    radar.add_field('specific_differential_attenuation', spec_diff_at,
                    replace_existing=True)
    radar.add_field('path_integrated_differential_attenuation', pida_dict,
                    replace_existing=True)
    radar.add_field('corrected_differential_reflectivity', cor_zdr,
                    replace_existing=True)

    # Py-ART's field metadata puts valid_min/valid_max on specific_attenuation
    # but none on specific_differential_attenuation, so AH above the cap is
    # silently masked on read while the ADP derived from that same AH is not.
    # Set both, deriving the ADP bound from the AH bound through the
    # ADP = c * AH ** d relation used to compute it, so the pair always masks
    # the same gates.
    ah_valid_max = float(cmac_config.get('specific_attenuation_valid_max', 1.0))
    radar.fields['specific_attenuation']['valid_min'] = 0.0
    radar.fields['specific_attenuation']['valid_max'] = ah_valid_max
    radar.fields['specific_differential_attenuation']['valid_min'] = 0.0
    radar.fields['specific_differential_attenuation']['valid_max'] = float(
        np.round(c_coef * ah_valid_max ** d_coef, 4))
    
    radar.fields['corrected_velocity']['units'] = 'm/s'
    if 'valid_min' not in radar.fields['corrected_velocity'].keys():
        radar.fields['corrected_velocity']['valid_min'] = cmac_config.get(
            'corrected_velocity_valid_min', -100.0)

    if 'valid_max' not in radar.fields['corrected_velocity'].keys():
        radar.fields['corrected_velocity']['valid_max'] = cmac_config.get(
            'corrected_velocity_valid_max', 100.0)

    radar.fields['corrected_velocity']['valid_min'] = np.round(
        radar.fields['corrected_velocity']['valid_min'], 4)
    radar.fields['corrected_velocity']['valid_max'] = np.round(
        radar.fields['corrected_velocity']['valid_max'], 4)
    radar.fields['simulated_velocity']['units'] = 'm/s'
    radar.fields['velocity_texture']['units'] = 'm/s'
    # BNF radar does not have "unfolded_differential_phase"
    radar.fields['unfolded_differential_phase']['long_name'] = 'Unfolded differential propagation phase shift'
    cat_dict = {}
    for pair_str in radar.fields['gate_id']['notes'].split(','):
        if verbose:
            print(pair_str)
        cat_dict.update({pair_str.split(':')[1]: int(pair_str.split(':')[0])})

    rain_gates = pyart.correct.GateFilter(radar)
    rain_gates.exclude_all()
    rain_gates.include_equal('gate_id', cat_dict['rain'])
    rr_valid_max = cmac_config.get('rain_rate_valid_max', 400)
    print("Rainfall rate A")
    rr_a = cmac_config['rain_rate_a_coef_A']
    rr_b = cmac_config['rain_rate_b_coef_A']
    radar = rain_rate(radar, rr_a, rr_b, moment="specific_attenuation",
                      valid_max=rr_valid_max)
    print("Rainfall Rate KDP")
    rr_a = cmac_config['rain_rate_a_coef_Kdp']
    rr_b = cmac_config['rain_rate_b_coef_Kdp']
    radar = rain_rate(radar, rr_a, rr_b, moment="corrected_specific_diff_phase",
                      valid_max=rr_valid_max)
    print("Rainfall rate Z")
    rr_a = cmac_config['rain_rate_a_coef_Z']
    rr_b = cmac_config['rain_rate_b_coef_Z']
    radar = rain_rate(radar, rr_a, rr_b, moment="corrected_reflectivity",
                      valid_max=rr_valid_max)
    mask = cmac_gates.gate_excluded

    if snowfall == True:
        snow_gates = pyart.correct.GateFilter(radar)
        snow_gates.exclude_all()
        snow_gates.include_equal('gate_id', cat_dict['snow'])
        if verbose:
            print('## Rainfall rate as a function of A ##')

    
        sr_valid_max = cmac_config.get('snow_rate_valid_max', 500)
        for zs_key in zs_relationship_dict.keys():
            abbreviation = zs_relationship_dict[zs_key]["abbreviation"]
            A = zs_relationship_dict[zs_key]["A"]
            B = zs_relationship_dict[zs_key]["B"]
            radar = snow_rate(radar, 1 / snow_density, A, B, zs_key,
                              abbreviation, valid_max=sr_valid_max)
            radar.fields['snow_rate_%s' % abbreviation]['data'] = np.ma.masked_where(snow_gates.gate_excluded,
            radar.fields['snow_rate_%s' % abbreviation]['data'])


    # Calculating snowfall rate

    if verbose:
        print("## Snowfall rate from Z-S relationship")

    print('##')
    print('## All CMAC fields have been added to the radar object.')
    print('##')

    # Adding the metadata to the cmac radar object.
    print('## Appending metadata')
    command_line = ''
    for item in sys.argv:
        command_line = command_line + ' ' + item
    if meta_append is None or meta_append == 'default':
        meta = get_default_metadata(config_file=config_file)
    elif meta_append.lower().endswith('.json'):
        with open(meta_append, 'r') as infile:
            meta = json.load(infile)
    elif meta_append == 'config':
        meta = meta_config
    else:
        raise RuntimeError(
            "meta_append must be None, 'config', 'default', or a path "
            "to a .json file; got %r" % meta_append)

    radar.metadata.clear()
    radar.metadata.update(meta)
    radar.metadata['command_line'] = command_line
    # Which classifier produced gate_id is not recoverable from the field
    # itself once the categories have been folded, and every masked product in
    # the file depends on it, so it is recorded as provenance.
    radar.metadata['gate_id_method'] = gate_id_method
    if gate_id_meta is not None:
        radar.metadata['gate_id_temperature_source'] = str(
            gate_id_meta.get('temp_source'))
        # Which generation of each moment the classifier actually saw. Every
        # ARM volume publishes several candidates per moment, so this is not
        # recoverable from the file without it.
        radar.metadata['gate_id_classified_on'] = ', '.join(
            '%s=%s' % (logical, source) for logical, source
            in sorted(gate_id_meta.get('classified_on', {}).items()))
        radar.metadata['gate_id_no_evidence_gates'] = int(
            gate_id_meta['n_no_evidence'])
        # A volume the classifier declined folds to no_scatter, which reads as
        # clear air, so the count and the reason travel with the file.
        radar.metadata['gate_id_unclassified_gates'] = int(
            gate_id_meta.get('n_unclassified', 0))
        radar.metadata['gate_id_skipped_sweeps'] = '; '.join(
            'sweep %s (%s, elevation span %.1f deg)'
            % (entry.get('sweep'), entry.get('sweep_mode'),
               float(entry.get('elevation_span', float('nan'))))
            for entry in gate_id_meta.get('skipped_sweeps') or []) or 'none'
        if gate_id_meta.get('freezing_level_m') is not None:
            radar.metadata['gate_id_freezing_level_m'] = float(
                np.round(gate_id_meta['freezing_level_m'], 2))
    return radar


def area_coverage(radar, precip_threshold=None, convection_threshold=None,
                  config=None, config_file=None):
    """ Returns percent coverage of precipitation and convection.

    Thresholds default to the per-radar ``area_coverage_precip_threshold``
    and ``area_coverage_convection_threshold`` config values (10.0 and 40.0
    dBZ respectively) when not passed explicitly. Pass ``config`` (the
    radar config name) and optionally ``config_file`` to pull the defaults
    from a YAML override.
    """
    if precip_threshold is None or convection_threshold is None:
        if config is not None:
            cmac_config = get_cmac_values(config, config_file=config_file)
        else:
            cmac_config = {}
        if precip_threshold is None:
            precip_threshold = cmac_config.get(
                'area_coverage_precip_threshold', 10.0)
        if convection_threshold is None:
            convection_threshold = cmac_config.get(
                'area_coverage_convection_threshold', 40.0)
    temp_radar = radar.extract_sweeps([0])
    ref = temp_radar.fields['corrected_reflectivity']['data']
    total_len = len(ref.flatten())
    ref_10_len = len(np.argwhere(ref >= precip_threshold))
    ref_40_len = len(np.argwhere(ref >= convection_threshold))
    ref_10_per = (ref_10_len/total_len)*100
    ref_40_per = (ref_40_len/total_len)*100
    del temp_radar
    return ref_10_per, ref_40_per


def pbb_to_dict(pbb_all):
    """ Function that takes the pbb_all array and turns
    it into a dictionary to be used and added to the
    pyart radar object. """
    pbb_dict = {}
    pbb_dict['coordinates'] = 'elevation azimuth range'
    pbb_dict['units'] = '1'
    pbb_dict['data'] = pbb_all
    pbb_dict['standard_name'] = 'partial_beam_block'
    pbb_dict['long_name'] = 'Partial Beam Block Fraction'
    pbb_dict['comment'] = 'Partial beam block fraction due to terrain.'
    return pbb_dict


def cbb_to_dict(cbb_all):
    """ Function that takes the cbb_all array and turns
    it into a dictionary to be used and added to the
    pyart radar object. """
    cbb_dict = {}
    cbb_dict['coordinates'] = 'elevation azimuth range'
    cbb_dict['units'] = '1'
    cbb_dict['data'] = cbb_all
    cbb_dict['standard_name'] = 'cumulative_beam_block'
    cbb_dict['long_name'] = 'Cumulative Beam Block Fraction'
    cbb_dict['comment'] = 'Cumulative beam block fraction due to terrain.'
    return cbb_dict
