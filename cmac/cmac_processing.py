""" Module that does various CMAC calculations. This code was written by
Scott Collis and Robert Jackson. """

import copy
import datetime
import os
import time

from . import csu_kdp
import fnmatch
import netCDF4
import numpy as np
import pyart
from pyart.correct.phase_proc import det_sys_phase, det_sys_phase_gf
from scipy import integrate
from scipy import ndimage, interpolate
import skfuzzy as fuzz
import wradlib as wrl

rain_rate_abbrevs = {'specific_attenuation': 'A',
                     'corrected_specific_diff_phase': 'Kdp',
                     'corrected_reflectivity': 'Z'}

def rain_rate(radar, A, B, moment="specific_attenuation", valid_max=400):
    """
    Rain rate applied to a pyart Radar object.

    Takes a given set of an A coefficient and a B exponent to a
    rainfall rate estimator based off of the given moment. The rainfall rate will
    then be calculated using R = A(Moment)^B.
    """

    if not moment in rain_rate_abbrevs.keys():
        raise ValueError(f"Invalid moment: {moment}")
    else:
        abbrev = rain_rate_abbrevs[moment]

    mom = radar.fields[moment]["data"]
    if moment == "corrected_reflectivity":
        mom = 10**(mom / 10.)
    rr = A * mom ** B
    print(moment)
    radar.add_field_like(moment, f'rain_rate_{abbrev}', rr, replace_existing=True)
    radar.fields[f'rain_rate_{abbrev}']['units'] = 'mm/h'
    radar.fields[f'rain_rate_{abbrev}']['standard_name'] = 'rainfall_rate'
    radar.fields[f'rain_rate_{abbrev}']['long_name'] = f'Rainfall rate estimated from {abbrev}'
    radar.fields[f'rain_rate_{abbrev}']['valid_min'] = 0
    radar.fields[f'rain_rate_{abbrev}']['valid_max'] = valid_max
    radar.fields[f'rain_rate_{abbrev}']['A_coefficient'] = A
    radar.fields[f'rain_rate_{abbrev}']['B_exponent'] = B
    return radar
    

def snow_rate(radar, swe_ratio, A, B, citation='Wolf and Snider 2012',
              abbrev='ws2012', valid_max=500):
    """
    Snow rate applied to a pyart.Radar object

    Takes a given Snow Water Equivilent ratio (swe_ratio), A and B value
    for the Z-S relationship and creates a radar field similar to DBZ
    showing the radar estimated snowfall rate in mm/hr. Then the given
    SWE_ratio, A and B are stored in the radar metadata for later
    reference.

    """
    # Setting up for Z-S relationship:
    snow_z = radar.fields['corrected_reflectivity']['data'].copy()
    # Convert it from dB to linear units
    z_lin = 10.0**(radar.fields['corrected_reflectivity']['data']/10.)
    # Apply the Z-S relation.
    snow_z = swe_ratio * (z_lin/A)**(1./B)
    # Add the field back to the radar. Use reflectivity as a template
    radar.add_field_like('corrected_reflectivity', 'snow_rate_%s' % abbrev,  snow_z,
                         replace_existing=True)
    # Update units and metadata
    radar.fields['snow_rate_%s' % abbrev]['units'] = 'mm/h'
    radar.fields['snow_rate_%s' % abbrev]['standard_name'] = 'snowfall_rate'
    radar.fields['snow_rate_%s' % abbrev]['long_name'] = 'Snowfall rate from Z using %s' % citation
    radar.fields['snow_rate_%s' % abbrev]['valid_min'] = 0
    radar.fields['snow_rate_%s' % abbrev]['valid_max'] = valid_max
    radar.fields['snow_rate_%s' % abbrev]['swe_ratio'] = swe_ratio
    radar.fields['snow_rate_%s' % abbrev]['A'] = A
    radar.fields['snow_rate_%s' % abbrev]['B'] = B
    return radar


def snr_and_sounding(radar, soundings_dir, override_file=None, verbose=True):
    if override_file is None:
        radar_start_date = netCDF4.num2date(radar.time['data'][0],
                                            radar.time['units'])
        sonde_pattern = datetime.datetime.strftime(
            radar_start_date, 'sgpgriddedsondeC1.c0.%Y%m%d.*')
        all_sonde_files = os.listdir(soundings_dir)
        sonde_name = fnmatch.filter(all_sonde_files, sonde_pattern)[0]
        print(sonde_pattern, sonde_name)
        interp_sonde = netCDF4.Dataset(os.path.join(soundings_dir, sonde_name))
    else:
        sonde_name = override_file
        interp_sonde = netCDF4.Dataset(sonde_name)

    temperatures = interp_sonde.variables['temp'][:]
    times = interp_sonde.variables['time'][:]
    heights = interp_sonde.variables['height'][:]
    my_profile = pyart.retrieve.fetch_radar_time_profile(interp_sonde, radar)
    if verbose:
        print(my_profile['temp'].shape)
        print(my_profile['height'])
    info_dict = {'long_name': 'Sounding temperature at gate',
                 'standard_name': 'temperature',
                 'valid_min': -100,
                 'valid_max': 100,
                 'units': 'degrees Celsius'}
    z_dict, temp_dict = pyart.retrieve.map_profile_to_gates(
        my_profile['temp'], my_profile['height'] * 1000.0, radar)
    snr = pyart.retrieve.calculate_snr_from_reflectivity(radar)
    return z_dict, temp_dict, snr


def get_texture(radar, vel_field, nyq=None, window=4, median_size=(4, 4)):
    """ Calculates velocity texture field. """
    if nyq is None:
        nyq = radar.instrument_parameters['nyquist_velocity']['data'][0]
    else:
        nyq = nyq
    start_time = time.time()
    if 'ground_clutter' in radar.fields.keys():
        vel = np.ma.masked_where(radar.fields['ground_clutter']['data'] == 1,
                                 radar.fields[vel_field]['data'])
        vel = vel.filled(np.nan)
    else:
        vel = radar.fields[vel_field]['data']

    std_dev = pyart.util.angular_texture_2d(vel, window, nyq)
    filtered_data = ndimage.filters.median_filter(std_dev, size=tuple(median_size))
    texture_field = pyart.config.get_metadata('velocity')
    texture_field['data'] = np.ma.masked_where(
        np.isnan(filtered_data), filtered_data)
    total_time = time.time() - start_time
    return texture_field


# Moment : [[start_up, finish_up, start_down, finish_down], weight]
def cum_score_fuzzy_logic(radar, mbfs=None,
                          ret_scores=False,
                          hard_const=None,
                          verbose=False,
                          median_size=(3, 4)):
    if mbfs is None:
        second_trip = {'velocity_texture': [[0, 0, 1.8, 2], 1.0],
                       'cross_correlation_ratio': [[.5, .7, 1, 1], 0.0],
                       'normalized_coherent_power': [[0, 0, .5, .6], 3.0],
                       'height': [[0, 0, 5000, 8000], 1.0],
                       'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                       'signal_to_noise_ratio': [[15, 20, 1000, 1000], 1.0]}

        rain = {'differential_phase_texture': [[0, 0, 80, 90], 1.0],
                'cross_correlation_ratio': [[0.94, 0.96, 1, 1], 1.0],
                'normalized_coherent_power': [[0.4, 0.5, 1, 1], 1.0],
                'height': [[0, 0, 5000, 6000], 0.0],
                'sounding_temperature': [[0, 3, 100, 100], 2.0],
                'signal_to_noise_ratio': [[8, 10, 1000, 1000], 1.0]}

        snow = {'differential_phase_texture': [[0, 0, 80, 90], 1.0],
                'cross_correlation_ratio': [[0.85, 0.9, 1, 1], 1.0],
                'normalized_coherent_power': [[0.4, 0.5, 1, 1], 1.0],
                'height': [[0, 0, 25000, 25000], 0.0],
                'sounding_temperature': [[-100, -100, 0, 1.], 2.0],
                'signal_to_noise_ratio': [[8, 10, 1000, 1000], 1.0]}

        no_scatter = {'differential_phase_texture': [[90, 90, 400, 400], 0.0],
                      'cross_correlation_ratio': [[0, 0, 0.1, 0.2], 0.0],
                      'normalized_coherent_power': [[0, 0, 0.1, 0.2], 0.0],
                      'height': [[0, 0, 25000, 25000], 0.0],
                      'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                      'signal_to_noise_ratio': [[-100, -100, 8, 10], 6.0]}

        melting = {'differential_phase_texture': [[20, 30, 80, 90], 0.0],
                   'cross_correlation_ratio': [[0.6, 0.7, .94, .96], 4.],
                   'normalized_coherent_power': [[0.4, 0.5, 1, 1], 0],
                   'height': [[0, 0, 25000, 25000], 0.0],
                   'sounding_temperature': [[-1., 0, 3.5, 5], 2.],
                   'signal_to_noise_ratio': [[8, 10, 1000, 1000], 0.0]}

        mbfs = {'multi_trip': second_trip, 'rain': rain, 'snow': snow,
                'no_scatter': no_scatter, 'melting': melting}

    flds = radar.fields
    scores = {}
    for key in mbfs.keys():
        if verbose:
            print('##    Doing', key)
        this_score = np.zeros(
            flds[list(flds.keys())[0]]['data'].shape).flatten() * 0.0
        for MBF in mbfs[key].keys():
            this_score = fuzz.trapmf(
                flds[MBF]['data'].flatten(),
                mbfs[key][MBF][0]) * mbfs[key][MBF][1] + this_score

        this_score = this_score.reshape(
            flds[list(flds.keys())[0]]['data'].shape)
        scores.update({key: ndimage.filters.median_filter(
            this_score, size=list(median_size))})

    if hard_const is not None:
        # hard_const = [[class, field, (v1, v2)], ...]
        for this_const in hard_const:
            if verbose:
                print('##    Doing hard constraining', this_const[0])
            key = this_const[0]
            const = this_const[1]
            fld_data = radar.fields[const]['data']
            lower = this_const[2][0]
            upper = this_const[2][1]
            const_area = np.where(np.logical_and(fld_data >= lower,
                                                 fld_data <= upper))
            if verbose:
                print('##    ', str(const_area))
            scores[key][const_area] = 0.0
    stacked_scores = np.dstack([scores[key] for key in scores.keys()])
    #sum_of_scores = stacked_scores.sum(axis = 2)
    #print(sum_of_scores.shape)
    #norm_stacked_scores = stacked_scores
    max_score = stacked_scores.argmax(axis=2)

    gid = {}
    gid['data'] = max_score
    gid['units'] = ''
    strgs = ''
    i = 0
    for key in scores.keys():
        strgs = strgs + str(i) + ':' + key + ','
        i = i + 1
    gid['long_name'] = 'Classification of dominant scatterer'
    gid['notes'] = strgs[0:-1]
    gid['valid_max'] = max_score.max()
    gid['valid_min'] = 0.0

    if ret_scores is False:
        rv = (gid, scores.keys())
    else:
        rv = (gid, scores.keys(), scores)
    return rv


def do_my_fuzz(radar, rhv_field, ncp_field,
               tex_start=2.0, tex_end=2.1,
               custom_mbfs=None, custom_hard_constraints=None,
               verbose=True, median_size=(3, 4)):  # NEEDS DOCSTRING
    if verbose:
        print('##')
        print('## CMAC calculation using fuzzy logic:')

    second_trip = {'velocity_texture': [[tex_start, tex_end, 130., 130.], 4.0],
                   rhv_field: [[.5, .7, 1, 1], 0.0],
                   ncp_field: [[0, 0, .5, .6], 1.0],
                   'height': [[0, 0, 5000, 8000], 0.0],
                   'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                   'signal_to_noise_ratio': [[5, 10, 1000, 1000], 1.0]}

    rain = {'velocity_texture': [[0, 0, tex_start, tex_end], 1.0],
            rhv_field: [[0.97, 0.98, 1, 1], 1.0],
            ncp_field: [[0.4, 0.5, 1, 1], 1.0],
            'height': [[0, 0, 5000, 6000], 0.0],
            'sounding_temperature': [[2., 5., 100, 100], 2.0],
            'signal_to_noise_ratio': [[8, 10, 1000, 1000], 1.0]}

    snow = {'velocity_texture': [[0, 0, tex_start, tex_end], 1.0],
            rhv_field: [[0.65, 0.9, 1, 1], 1.0],
            ncp_field: [[0.4, 0.5, 1, 1], 1.0],
            'height': [[0, 0, 25000, 25000], 0.0],
            'sounding_temperature': [[-100, -100, .5, 4.], 2.0],
            'signal_to_noise_ratio': [[8, 10, 1000, 1000], 1.0]}

    no_scatter = {'velocity_texture': [[tex_start, tex_end, 330., 330.], 2.0],
                  rhv_field: [[0, 0, 0.1, 0.2], 0.0],
                  ncp_field: [[0, 0, 0.1, 0.2], 0.0],
                  'height': [[0, 0, 25000, 25000], 0.0],
                  'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                  'signal_to_noise_ratio': [[-100, -100, 5, 10], 4.0]}

    melting = {'velocity_texture': [[0, 0, tex_start, tex_end], 0.0],
               rhv_field: [[0.6, 0.65, .9, .96], 2.0],
               ncp_field: [[0.4, 0.5, 1, 1], 0],
               'height': [[0, 0, 25000, 25000], 0.0],
               'sounding_temperature': [[0, 0.1, 2, 4], 4.0],
               'signal_to_noise_ratio': [[8, 10, 1000, 1000], 0.0]}

    if custom_mbfs is None:
        mbfs = {'multi_trip': second_trip, 'rain': rain, 'snow': snow,
                'no_scatter': no_scatter, 'melting': melting}
    else:
        mbfs = custom_mbfs

    if custom_hard_constraints is None:
        hard_const = [['melting', 'sounding_temperature', (10, 100)],
                      ['multi_trip', 'height', (10000, 1000000)],
                      ['melting', 'sounding_temperature', (-10000, -2)],
                      ['rain', 'sounding_temperature', (-1000, -5)],
                      ['melting', 'velocity_texture', (3, 300)]]
    else:
        hard_const = custom_hard_constraints

    gid_fld, cats = cum_score_fuzzy_logic(radar, mbfs=mbfs, verbose=verbose,
                                          hard_const=hard_const,
                                          median_size=median_size)
    rain_val = list(cats).index('rain')
    snow_val = list(cats).index('snow')
    melt_val = list(cats).index('melting')
    return _fix_rain_above_bb(gid_fld, rain_val, melt_val, snow_val), cats


def get_melt(radar, melt_cat=None, fzl_ceiling=5000.0,
             fzl_replacement=3500.0, fzl_floor=1000.0):
    if melt_cat is None:
        cat_dict = {}
        for pair_str in radar.fields['gate_id']['notes'].split(','):
            cat_dict.update(
                {pair_str.split(':')[1]: int(pair_str.split(':')[0])})

        melt_cat = cat_dict['melting']

    melt_locations = np.where(radar.fields['gate_id']['data'] == melt_cat)
    kinda_cold = np.ma.where(np.logical_and(
        radar.fields['sounding_temperature']['data'] > -30, radar.fields['sounding_temperature']['data'] < 0))
    fzl_sounding = radar.gate_altitude['data'][kinda_cold].min()
    if len(melt_locations[0] > 1):
        fzl_pid = radar.gate_altitude['data'][melt_locations].min()
        fzl = (fzl_pid + fzl_sounding) / 2.0
    else:
        fzl = fzl_sounding

    print(fzl)
    if fzl > fzl_ceiling:
        fzl = fzl_replacement
    if fzl < fzl_floor:
        fzl = radar.gate_altitude['data'].min()
    return fzl

def get_sys_phase(radar, gatefilter=None, phidp_field='differential_phase',
                  ncp_field='normalized_coherent_power',
                  rhv_field='copol_correlation_coeff', first_gate=30,
                  n_gates=25, min_gates=10, min_rays=10):
    """
    Estimate the PhiDP system phase offset in degrees.

    Takes the median PhiDP over the first n_gates meteorological gates of
    each ray, then the median of those across rays. The median is used in
    preference to the per-ray minimum that Py-ART's estimators take because
    PhiDP here is noisy enough (gate to gate standard deviation of order 30
    degrees) that a minimum sits well below the true offset.

    The Py-ART estimators are kept as fallbacks. Both walk the rays of the
    first sweep, so they raise IndexError on volumes whose
    sweep_end_ray_index disagrees with the actual ray count, which is the
    case for some of the BNF RHI files.

    Returns None if no estimate can be made, in which case the caller should
    leave PhiDP alone.

    """
    phidp = radar.fields[phidp_field]['data'][:, first_gate:]
    if gatefilter is not None:
        included = gatefilter.gate_included[:, first_gate:]
    else:
        included = ~np.ma.getmaskarray(phidp)

    values = np.ma.filled(phidp, np.nan)
    phases = []
    for ray in range(values.shape[0]):
        good = values[ray][included[ray] & np.isfinite(values[ray])]
        if good.size >= min_gates:
            phases.append(np.median(good[:n_gates]))
    if len(phases) >= min_rays:
        return float(np.median(phases))

    for estimator in (
            lambda: det_sys_phase_gf(radar, gatefilter,
                                     phidp_field=phidp_field,
                                     first_gate=int(first_gate)),
            lambda: det_sys_phase(radar, ncp_field=ncp_field,
                                  rhv_field=rhv_field,
                                  phidp_field=phidp_field)):
        try:
            sys_phase = estimator()
        except (KeyError, IndexError, ValueError, TypeError):
            continue
        if sys_phase is not None and np.isfinite(sys_phase):
            return float(sys_phase)
    return None


def remove_sys_phase(phidp, sys_phase, wrap_min=-90.0):
    """
    Subtract the system phase offset from PhiDP and undo the 0-360 fold.

    PhiDP is measured modulo 360, so subtracting the offset and taking the
    remainder recovers the propagation phase in a single step. The result is
    wrapped into [wrap_min, wrap_min + 360) rather than [0, 360) so that
    noise about zero at close range stays slightly negative instead of
    folding up to nearly 360 degrees.

    """
    return np.mod(phidp - sys_phase - wrap_min, 360.0) + wrap_min


def fix_phase_fields(orig_kdp, orig_phidp, rrange, happy_kdp,
                     max_kdp=15.0):
    kdp_data = np.ma.asanyarray(orig_kdp['data'])
    phidp_data = np.ma.asanyarray(orig_phidp['data'])
    mask = (np.ma.getmaskarray(kdp_data) |
            np.ma.getmaskarray(phidp_data) |
            happy_kdp.gate_excluded)
    kdp_values = np.ma.filled(kdp_data, 0.0).copy()
    kdp_values[happy_kdp.gate_excluded] = 0.0
    kdp_values[kdp_values > max_kdp] = max_kdp
    interg = integrate.cumulative_trapezoid(kdp_values, rrange, axis=1)
    phidp_values = np.ma.filled(phidp_data, 0.0).copy()
    phidp_values[:, 0:-1] = interg/len(rrange)
    orig_kdp['data'] = np.ma.array(kdp_values, mask=mask)
    orig_phidp['data'] = np.ma.array(phidp_values, mask=mask)
    return orig_phidp, orig_kdp


def synchronize_phase_field_masks(phidp, kdp):
    """Give a phase field and its KDP field the same gate mask.

    Differential phase and specific differential phase are generated by
    separate Py-ART/CMAC paths.  Those paths can preserve different masks,
    even though the fields describe the same gates and are consumed as a
    pair by downstream products.  Preserve every masked gate from either
    input so neither field exposes a value where its companion is masked.

    The field dictionaries are modified in place and returned for convenient
    use by callers.
    """
    phidp_data = np.ma.asanyarray(phidp['data'])
    kdp_data = np.ma.asanyarray(kdp['data'])
    mask = np.logical_or(
        np.ma.getmaskarray(phidp_data), np.ma.getmaskarray(kdp_data))
    phidp['data'] = np.ma.array(phidp_data, mask=mask, copy=False)
    kdp['data'] = np.ma.array(kdp_data, mask=mask, copy=False)
    return phidp, kdp


def return_csu_kdp(radar):
    dzN = _extract_unmasked_data(radar, 'reflectivity')
    dpN = _extract_unmasked_data(radar, 'differential_phase')
    # Range needs to be supplied as a variable, and it needs to be
    # the same shape as dzN, etc.
    rng2d, az2d = np.meshgrid(radar.range['data'], radar.azimuth['data'])
    bt = time.time()
    kdN, fdN, sdN = csu_kdp.calc_kdp_bringi(
        dp=dpN, dz=dzN, rng=rng2d/1000.0, thsd=12, gs=250.0, window=5)
    print(time.time()-bt, 'seconds to run')
    csu_kdp_field = _csu_to_field(
        kdN, radar, units='deg/km', long_name='Specific Differential Phase',
        standard_name='Specific Differential Phase', dz_field='reflectivity')
    csu_filt_dp = _csu_to_field(
        fdN, radar, units='deg', long_name='Filtered Differential Phase',
        standard_name='Filtered Differential Phase', dz_field='reflectivity')
    csu_kdp_sd = _csu_to_field(
        sdN, radar, units='deg',
        long_name='Standard Deviation of Differential Phase',
        standard_name='Standard Deviation of Differential Phase',
        dz_field='reflectivity')
    return  csu_kdp_field, csu_filt_dp, csu_kdp_sd


def retrieve_qvp(radar, hts, flds=None):
    """ Calculates a quasi-vertical profile. """
    if flds is None:
        flds = ['differential_phase', 'cross_correlation_ratio',
                'spectrum_width', 'reflectivity',
                'differential_reflectivity']
    desired_angle = 20.0
    index = abs(radar.fixed_angle['data'] - desired_angle).argmin()
    ss = radar.sweep_start_ray_index['data'][index]
    se = radar.sweep_end_ray_index['data'][index]
    mid = int((ss+se)/2)
    z = radar.gate_altitude['data'][mid, :]
    qvp = {}
    for fld in flds:
        this_fld = radar.get_field(index, fld)[:, :].mean(axis=0)
        intery = interpolate.interp1d(
            z, this_fld, bounds_error=False, fill_value='extrapolate')
        ithis = intery(hts)
        qvp.update({fld:ithis})
    qvp.update({'time': radar.time})
    qvp.update({'height': hts})
    return qvp


def _fix_rain_above_bb(gid_fld, rain_class, melt_class, snow_class):
    print(snow_class)
    new_gid = copy.deepcopy(gid_fld)
    for ray_num in range(new_gid['data'].shape[0]):
        if melt_class in new_gid['data'][ray_num, :]:
            max_loc = np.where(
                new_gid['data'][ray_num, :] == melt_class)[0].max()
            rain_above_locs = np.where(
                new_gid['data'][ray_num, max_loc:] == rain_class)[0] + max_loc
            new_gid['data'][ray_num, rain_above_locs] = snow_class
    return new_gid


def _extract_unmasked_data(radar, field, bad=-32768):
    """ Simplify getting unmasked radar fields from Py-ART. """
    return radar.fields[field]['data'].filled(fill_value=bad)


def _csu_to_field(field, radar, units='unitless', long_name='Hydrometeor ID',
                  standard_name='Hydrometeor ID', dz_field='ZC'):
    """ Adds a newly created field to the Py-ART radar object. If reflectivity
    is a masked array, make the new field masked the same as reflectivity. """
    fill_value = -32768
    masked_field = np.ma.asanyarray(field)
    masked_field.mask = masked_field == fill_value
    if hasattr(radar.fields[dz_field]['data'], 'mask'):
        setattr(masked_field, 'mask',
                np.logical_or(
                    masked_field.mask, radar.fields[dz_field]['data'].mask))
        fill_value = radar.fields[dz_field]['_FillValue']
    field_dict = {'data': masked_field,
                  'units': units,
                  'long_name': long_name,
                  'standard_name': standard_name,
                  '_FillValue': fill_value}
    return field_dict


def gen_clutter_field_from_refl(radar, corrected_field, uncorrected_field, diff_dbz=-12.0, max_h=2000.0):
    """
    Generate a Py-ART field with clutter flagging using
    differences in reflectivity. A cludge for when you
    have a clutter corrected field but no field with the
    flags

    Parameters
    ----------
    radar : Radar
        A radar object to create the clutter field from
    corrected_field : String
        Field name for a field which has had gates with clutter in them reduced some how
    uncorrected_field : String
        Field name for raw reflectivity field
    diff_dbz : float
        Difference in dBZ below which a gate is considered clutter. Defaiults to -12dBZ
    max_h : float
        Height (in m) above which all gates are considered to be clutter free.

    Returns
    clutter_field : Dict
        A field dictionary whith an entry 'data' where clutter is flagged as '1' and clutter
        free is flagged as '0'
    """
    new_grid = radar.fields[
        'attenuation_corrected_reflectivity_h']['data'] - radar.fields[
            'reflectivity']['data']
    clutter = np.zeros(new_grid.shape, dtype=int)
    possible_contamination = new_grid < diff_dbz
    clutter[possible_contamination] = 1

    z = radar.gate_altitude['data']
    clutter[(z - z.min()) > max_h] = 0

    clutter_field = {'data': clutter,
                     'long_name': 'Clutter mask',
                     'comment': '0 is good, 1 is clutter',
                     'valid_min': 0,
                     'valid_max': 1,
                     'units': '1',
                     'flag_values': [0, 1],
                     'flag_meanings': 'no_clutter clutter'}

    return clutter_field


def beam_block(radar, tif_file, radar_height_offset=10.0,
               beam_width=1.0):
    """
    Beam Block Radar Calculation.

    Parameters
    ----------
    radar : Radar
        Radar object used.
    tif_name : string
        Name of geotiff file to use for the
        calculation.
    radar_height_offset : float
        Add height to the radar altitude for radar towers.

    Other Parameters
    ----------------
    beam_width : float
        Radar's beam width for calculation.
        Default value is 1.0.

    Returns
    -------
    pbb_all : array
        Array of partial beam block fractions for each
        gate in all sweeps.
    cbb_all : array
        Array of cumulative beam block fractions for
        each gate in all sweeps.

    References
    ----------
    Bech, J., B. Codina, J. Lorente, and D. Bebbington,
    2003: The sensitivity of single polarization weather
    radar beam blockage correction to variability in the
    vertical refractivity gradient. J. Atmos. Oceanic
    Technol., 20, 845–855

    Heistermann, M., Jacobi, S., and Pfaff, T., 2013:
    Technical Note: An open source library for processing
    weather radar data (wradlib), Hydrol. Earth Syst.
    Sci., 17, 863-871, doi:10.5194/hess-17-863-2013

    Helmus, J.J. & Collis, S.M., (2016). The Python ARM
    Radar Toolkit (Py-ART), a Library for Working with
    Weather Radar Data in the Python Programming Language.
    Journal of Open Research Software. 4(1), p.e25.
    DOI: http://doi.org/10.5334/jors.119
    """
    # Opening the tif file and getting the values ready to be
    # converted into polar values.
    rasterfile = tif_file
    data_raster = wrl.io.open_raster(rasterfile)
    rastervalues, rastercoords, proj = wrl.georef.extract_raster_dataset(
        data_raster, nodata=None)
    #rastervalues_, rastercoords_, crs = wrl.georef.extract_raster_dataset(data_raster, nodata=-32768.)
    sitecoords = (np.float(radar.longitude['data']),
                  np.float(radar.latitude['data']),
                  np.float(radar.altitude['data'] + radar_height_offset))
    pbb_arrays = []
    cbb_arrays = []
    _range = radar.range['data']
    beamradius = wrl.util.half_power_radius(_range, beam_width)
    # Cycling through all sweeps in the radar object.
    print('Calculating beam blockage.')
    for i in range(len(radar.sweep_start_ray_index['data'])):
        index_start = radar.sweep_start_ray_index['data'][i]
        index_end = radar.sweep_end_ray_index['data'][i] + 1
        elevs = radar.elevation['data'][index_start:index_end]
        azimuths = radar.azimuth['data'][index_start:index_end]
        rg, azg = np.meshgrid(_range, azimuths)
        rg, eleg = np.meshgrid(_range, elevs)
        nrays = azimuths.shape[0]                        # number of rays
        nbins = radar.ngates                             # number of range bins
        bw = beam_width                                  # half power beam width (deg)
        range_res = radar.range['meters_between_gates']  # range resolution (meters)
        el = radar.fixed_angle['data'][i]
        coord = wrl.georef.sweep_centroids(nrays, range_res, nbins, el)
        coords = wrl.georef.spherical_to_proj(rg, azg, eleg,
                                              sitecoords, crs=crs)
        lon = coords[..., 0]
        lat = coords[..., 1]
        alt = coords[..., 2]
        polcoords = coords[..., :2]
        rlimits = (lon.min(), lat.min(), lon.max(), lat.max())

        #Clip the region inside our bounding box
        ind = wrl.util.find_bbox_indices(rastercoords, rlimits)
        rastercoords = rastercoords[ind[0]:ind[3], ind[0]:ind[2], ...]
        rastervalues = rastervalues[ind[0]:ind[3], ind[0]:ind[2]]
        polarvalues = wrl.ipol.cart_to_irregular_spline(
            rastercoords, rastervalues, polcoords, order=3,
            prefilter=False)
        # Calculate partial beam blockage using wradlib.
        pbb = wrl.qual.beam_block_frac(polarvalues, alt, beamradius)
        pbb = np.ma.masked_invalid(pbb)
        pbb_arrays.append(pbb)
        # Calculate cumulative beam blockage using wradlib.
        cbb = wrl.qual.cum_beam_block_frac(pbb)
        cbb_arrays.append(cbb)
    pbb_all = np.ma.concatenate(pbb_arrays)
    cbb_all = np.ma.concatenate(cbb_arrays)
    del data_raster
    return pbb_all, cbb_all
