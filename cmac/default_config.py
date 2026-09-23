"""
Configuration file for the Corrected Moments Antenna Coordinates (CMAC).

The values for a number of parameters that change depending on which radar is
being used.

"""



##############################################################################
# Default metadata
#
# The DEFAULT_METADATA dictionary contains dictionaries which provide the
# default metadata for each radar.
##############################################################################

_DEFAULT_METADATA = {
    # X-SAPR I6 PPI metadata.
    'xsapr_i6_ppi': {
        'site_id': 'sgp',
        'facility_id': 'I6' + ': ' + 'Deer Creek, OK',
        'data_level': 'c1',
        'comment': (
            'This is highly experimental and initial data. There are many',
            'known and unknown issues. Please do not use before',
            'contacting the Translator responsible scollis@anl.gov'),
        'attributions': (
            'This data is collected by the ARM Climate Research facility.',
            'Radar system is operated by the radar engineering team',
            'radar@arm.gov and the data is processed by the precipitation',
            'radar products team. LP code courtesy of Scott Giangrande BNL.'),
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': ('Nitin Bharadwaj, PNNL. Bradley Isom, PNNL.',
                    'Joseph Hardin, PNNL. Iosif Lindenmaier, PNNL.')},

    # X-SAPR I5 PPI metadata.
    'xsapr_i5_ppi': {
        'site_id': 'sgp',
        'facility_id': 'I5' + ': ' + 'Garber, OK',
        'data_level': 'c1',
        'comment': (
            'This is highly experimental and initial data. There are many',
            'known and unknown issues. Please do not use before',
            'contacting the Translator responsible scollis@anl.gov'),
        'attributions': (
            'This data is collected by the ARM Climate Research facility.',
            'Radar system is operated by the radar engineering team',
            'radar@arm.gov and the data is processed by the precipitation',
            'radar products team. LP code courtesy of Scott Giangrande BNL.'),
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': ('Nitin Bharadwaj, PNNL. Bradley Isom, PNNL.',
                    'Joseph Hardin, PNNL. Iosif Lindenmaier, PNNL.')},

    # X-SAPR I5 PPI metadata.
    'xsapr_i5_cfr_ppi': {
        'site_id': 'sgp',
        'facility_id': 'I5' + ': ' + 'Garber, OK',
        'data_level': 'c1',
        'comment': (
            'This is highly experimental and initial data. There are many',
            'known and unknown issues. Please do not use before',
            'contacting the Translator responsible scollis@anl.gov'),
        'attributions': (
            'This data is collected by the ARM Climate Research facility.',
            'Radar system is operated by the radar engineering team',
            'radar@arm.gov and the data is processed by the precipitation',
            'radar products team. LP code courtesy of Scott Giangrande BNL.'),
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': ('Nitin Bharadwaj, PNNL. Bradley Isom, PNNL.',
                    'Joseph Hardin, PNNL. Iosif Lindenmaier, PNNL.')},

    # X-SAPR I4 PPI metadata.
    'xsapr_i4_ppi': {
        'site_id': 'sgp',
        'facility_id': 'I4' + ': ' + 'Billings, OK',
        'data_level': 'c1',
        'comment': (
            'This is highly experimental and initial data. There are many',
            'known and unknown issues. Please do not use before',
            'contacting the Translator responsible scollis@anl.gov'),
        'attributions': (
            'This data is collected by the ARM Climate Research facility.',
            'Radar system is operated by the radar engineering team',
            'radar@arm.gov and the data is processed by the precipitation',
            'radar products team. LP code courtesy of Scott Giangrande BNL.'),
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': ('Nitin Bharadwaj, PNNL. Bradley Isom, PNNL.',
                    'Joseph Hardin, PNNL. Iosif Lindenmaier, PNNL.')},

    # X-SAPR I6 Sector metadata.
    'xsapr_i6_sec': {
        'site_id': 'sgp',
        'facility_id': 'I6' + ': ' + 'Deer Creek, OK',
        'data_level': 'c1',
        'comment': (
            'This is highly experimental and initial data. There are many',
            'known and unknown issues. Please do not use before',
            'contacting the Translator responsible scollis@anl.gov'),
        'attributions': (
            'This data is collected by the ARM Climate Research facility.',
            'Radar system is operated by the radar engineering team',
            'radar@arm.gov and the data is processed by the precipitation',
            'radar products team. LP code courtesy of Scott Giangrande BNL.'),
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': ('Nitin Bharadwaj, PNNL. Bradley Isom, PNNL.',
                    'Joseph Hardin, PNNL. Iosif Lindenmaier, PNNL.')},

    # X-SAPR I5 Sector metadata.
    'xsapr_i5_sec': {
        'site_id': 'sgp',
        'facility_id': 'I5' + ': ' + 'Garber, OK',
        'data_level': 'c1',
        'comment': (
            'This is highly experimental and initial data. There are many',
            'known and unknown issues. Please do not use before',
            'contacting the Translator responsible scollis@anl.gov'),
        'attributions': (
            'This data is collected by the ARM Climate Research facility.',
            'Radar system is operated by the radar engineering team',
            'radar@arm.gov and the data is processed by the precipitation',
            'radar products team. LP code courtesy of Scott Giangrande BNL.'),
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': ('Nitin Bharadwaj, PNNL. Bradley Isom, PNNL.',
                    'Joseph Hardin, PNNL. Iosif Lindenmaier, PNNL.')},

    # X-SAPR I4 Sector metadata.
    'xsapr_i4_sec': {
        'site_id': 'sgp',
        'facility_id': 'I4' + ': ' + 'Billings, OK',
        'data_level': 'c1',
        'comment': (
            'This is highly experimental and initial data. There are many',
            'known and unknown issues. Please do not use before',
            'contacting the Translator responsible scollis@anl.gov'),
        'attributions': (
            'This data is collected by the ARM Climate Research facility.',
            'Radar system is operated by the radar engineering team',
            'radar@arm.gov and the data is processed by the precipitation',
            'radar products team. LP code courtesy of Scott Giangrande BNL.'),
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': ('Nitin Bharadwaj, PNNL. Bradley Isom, PNNL.',
                    'Joseph Hardin, PNNL. Iosif Lindenmaier, PNNL.')},

    # CACTI C-SAPR 2 metadata.
    'cacti_csapr2_ppi': {
        'site_id': 'cor',
        'facility_id': 'c1',
        'comment': 'This is highly experimental and initial data. There are '
                   + 'many known and unknown issues. Please do not use before '
                   + 'contacting the Translator responsible scollis@anl.gov',
        'attributions': 'This data is collected by the ARM Climate Research '
                        + 'facility. Radar system is operated by the radar '
                        + 'engineering team radar@arm.gov and the data is '
                        + 'processed by the precipitation radar products team. '
                        + 'LP code courtesy of Scott Giangrande BNL.',
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.',
            'Issues with some snow below melting layer.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': 'Bradley Isom, PNNL. Iosif Lindenmaier, PNNL.',
        'Conventions': 'CF/Radial instrument_parameters ARM-1.3',
        'references': 'See CSAPR2 Instrument Handbook',
        'source': 'Atmospheric Radiation Measurement (ARM) program C-band '
                  + 'Scanning ARM Precipitation Radar 2 (CSAPR2)',
        'institution': 'United States Department of Energy - '
                       + 'Atmospheric Radiation Measurement (ARM) program',
        'doi': '10.5439/1668872',},
    
    # CACTI C-SAPR 2 metadata.
    'tracer_csapr2_ppi': {
        'site_id': 'hou',
        'facility_id': 's2',
        'comment': 'This is highly experimental and initial data. There are '
                   + 'many known and unknown issues. Please do not use before '
                   + 'contacting the Translator responsible scollis@anl.gov',
        'attributions': 'This data is collected by the ARM Climate Research '
                        + 'facility. Radar system is operated by the radar '
                        + 'engineering team radar@arm.gov and the data is '
                        + 'processed by the precipitation radar products team. '
                        + 'LP code courtesy of Scott Giangrande BNL.',
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions. Still uses old',
            'Giangrande code.',
            'Issues with some snow below melting layer.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': 'Bradley Isom, PNNL. Iosif Lindenmaier, PNNL.',
        'Conventions': 'CF/Radial instrument_parameters ARM-1.3',
        'references': 'See CSAPR2 Instrument Handbook',
        'source': 'Atmospheric Radiation Measurement (ARM) program C-band '
                  + 'Scanning ARM Precipitation Radar 2 (CSAPR2)',
        'institution': 'United States Department of Energy - '
                       + 'Atmospheric Radiation Measurement (ARM) program',
        'doi': '10.5439/1668872',},
 

    # NSA X-SAPR 2 metadata.
    'nsa_xsapr_ppi': {
        'Conventions': 'CF/Radial instrument_parameters ARM-1.3',
        'site_id': 'nsa',
        'facility_id': 'C1',
        'comment': 'This is highly experimental and initial data. There are '
                   + 'many known and unknown issues. Please do not use before '
                   + 'contacting the Translator responsible scollis@anl.gov',
        'attributions': 'This data is collected by the ARM Climate Research '
                        + 'facility. Radar system is operated by the radar '
                        + 'engineering team radar@arm.gov and the data is '
                        + 'processed by the precipitation radar products team. '
                        + 'LP code courtesy of Scott Giangrande BNL.',
        'process_version': 'CMAC',
        'vap_name': 'cmac',
        'known_issues': 'False phidp jumps in insect regions. Still uses old '
                        + 'Giangrande code. Issues with some snow below '
                        + 'melting layer.',
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': 'Bradley Isom, PNNL. Iosif Lindenmaier, PNNL.',
        'references': 'See XSAPR Instrument Handbook',
        'source': 'Atmospheric Radiation Measurement (ARM) program X-band '
                  + 'Scanning ARM Precipitation Radar (XSAPR)',
        'institution': 'U.S. Department of Energy Atmospheric Radiation '
                       + 'Measurement (ARM) Climate Research Facility',
        'platform_id': 'xsaprcmacppi',
        'dod_version': 'xsaprcmacppi-c1-1.0',
        'input_datastream': 'nsaxsaprcfrppiC1.a1',
        'data_level': 'c1',
        'datastream': 'nsaxsaprcmacppiC1.c1',
        'location_description': 'North Slope of Alaska (NSA), Barrow, Alaska',
        'doi': '10.5439/1781398',},

     'bnf_csapr2_ppi': {
        'site_id': 'bnf',
        'facility_id': 's3',
        'comment': 'This is highly experimental and initial data. There are '
                   + 'many known and unknown issues. Please do not use before '
                   + 'contacting the Translator responsible scollis@anl.gov',
        'attributions': 'This data is collected by the ARM Research '
                        + 'facility. Radar system is operated by the radar '
                        + 'engineering team radar@arm.gov and the data is '
                        + 'processed by the precipitation radar products team. '
                        + 'LP code courtesy of Scott Giangrande BNL.',
        'version': '2.0 lite',
        'vap_name': 'cmac',
        'known_issues': (
            'False phidp jumps in insect regions.'
            + 'Issues with some snow below melting layer.'),
        'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
        'translator': 'Scott Collis, ANL.',
        'mentors': 'Bradley Isom, PNNL. Iosif Lindenmaier, PNNL.',
        'Conventions': 'CF/Radial instrument_parameters ARM-1.3',
        'references': 'See CSAPR2 Instrument Handbook',
        'source': 'Atmospheric Radiation Measurement (ARM) program C-band '
                  + 'Scanning ARM Precipitation Radar 2 (CSAPR2)',
        'institution': 'United States Department of Energy - '
                       + 'Atmospheric Radiation Measurement (ARM) program',
        'doi': '10.5439/1668872',}, 

    # SAIL X-band metadata.
    'sail_xband_ppi': {
        'Conventions': 'CF/Radial instrument_parameters ARM-1.3',
        'site_id': 'guc',
        'facility_id': 'S2',
        'comment': 'This is highly experimental and initial data. There are '
                   + 'many known and unknown issues. Please do not use before '
                   + 'contacting the Translator responsible scollis@anl.gov',
        'attributions': 'This data is collected by the ARM Climate Research '
                        + 'facility. Radar system is operated by the radar '
                        + 'engineering team radar@arm.gov and the data is '
                        + 'processed by the precipitation radar products team. '
                        + 'LP code courtesy of Scott Giangrande BNL.',
        'process_version': 'CMAC',
        'vap_name': 'cmac',
        'known_issues': 'False phidp jumps in insect regions. Still uses old '
                        + 'Giangrande code. Issues with some snow below '
                        + 'melting layer.',
        'developers': "Robert Jackson, ANL., Zachary Sherman, ANL., Maxwell Grover, ANL., Joseph OBrien, ANL.",
        'translator': 'Scott Collis, ANL.',
        'mentors': "https://www.arm.gov/connect-with-arm/organization/instrument-mentors/list#xprecipradar",
        'references': 'See XPRECIPRADAR Instrument Handbook',
        'source': "Colorado State University X-Band Precipitation Radar (XPRECIPRADAR) (DOI: 10.5439/1844501) ",
        'institution': 'U.S. Department of Energy Atmospheric Radiation '
                       + 'Measurement (ARM) Climate Research Facility',
        'platform_id': 'xprecipradarcmacppi',
        'dod_version': 'xprecipradarcmacppi-c1-2.0',
        'input_datastream': 'gucxprecipradarS2.00',
        'data_level': 'c1',
        'datastream': 'gucxprecipradarcmacppiS2.c1',
        'location_description': 'Gunnison, Colorado',
        'doi': '10.5439/1883164',},
}

##############################################################################
# Default field names
#
# The DEFAULT_FIELD_NAMES dictionary contains field names for each radar and
# sonde field names that will be used with that radar.
##############################################################################

_DEFAULT_FIELD_NAMES = {
    # X-SAPR I6 PPI field names.
    'xsapr_i6_ppi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',
        'input_phidp_field': 'differential_phase',
        'velocity': 'velocity',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',
        'refl_field': 'corrected_reflectivity'},
 
    # X-SAPR I5 PPI field names.
    'xsapr_i5_ppi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',
        'input_phidp_field': 'differential_phase',
        'velocity': 'velocity',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',
        'refl_field': 'corrected_reflectivity'},
    
    # X-SAPR I5 RHI field names.
    'xsapr_i5_rhi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',
        'input_phidp_field': 'differential_phase',
        'velocity': 'velocity',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',
        'refl_field': 'corrected_reflectivity'}, 
    
    'xsapr_i5_cfr_ppi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',
        'velocity': 'mean_doppler_velocity',
        'input_phidp_field': 'differential_phase',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio_hv',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',
        'refl_field': 'corrected_reflectivity'},

    # X-SAPR I4 PPI field names.
    'xsapr_i4_ppi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',
        'velocity': 'velocity',
        'input_phidp_field': 'differential_phase',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',
        'refl_field': 'corrected_reflectivity'},

    # X-SAPR I6 Sector field names.
    'xsapr_i6_sec': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',
        'velocity': 'velocity',
        'input_phidp_field': 'differential_phase',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',
        'refl_field': 'corrected_reflectivity'},

    # X-SAPR I5 Sector field names.
    'xsapr_i5_sec': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',
        'velocity': 'velocity',
        'input_phidp_field': 'differential_phase',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',
        'refl_field': 'corrected_reflectivity'},

    # X-SAPR I4 Sector field names.
    'xsapr_i4_sec': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',
        'velocity': 'velocity',
        'input_phidp_field': 'differential_phase',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',
        'refl_field': 'corrected_reflectivity'},

    # CACTI C-SAPR 2 field names.
    'cacti_csapr2_ppi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',  # need to change to input_reflectivity
        'velocity': 'mean_doppler_velocity',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'copol_correlation_coeff',
        'input_phidp_field': 'uncorrected_differential_phase',
        'input_clutter_corrected_reflectivity': 'reflectivity',
        'clutter': 'ground_clutter',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',  # output phidp, need to change
        'refl_field': 'corrected_reflectivity'},  # output Z field

    # BNF C-SAPR 2 field names.
    'bnf_csapr2_ppi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',  # need to change to input_reflectivity
        'velocity': 'mean_doppler_velocity',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'copol_correlation_coeff',
        'input_phidp_field': 'differential_phase',
        'input_clutter_corrected_reflectivity': 'reflectivity',
        'clutter': 'ground_clutter',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': 'signal_to_noise_ratio_copolar_h',
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'corrected_differential_phase',  # output phidp, need to change
        'refl_field': 'corrected_reflectivity'},  # output Z field

    # CACTI C-SAPR 2 field names.
    'tracer_csapr2_ppi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',  # need to change to input_reflectivity
        'velocity': 'mean_doppler_velocity',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'copol_correlation_coeff',
        'input_phidp_field': 'uncorrected_differential_phase',
        'input_clutter_corrected_reflectivity': 'reflectivity',
        'clutter': 'ground_clutter',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',  # output phidp, need to change
        'refl_field': 'corrected_reflectivity'},  # output Z field
 
    # NSA X-SAPR 2 field names.
    'nsa_xsapr_ppi': {
        # Radar field names
        'input_zdr': 'differential_reflectivity',
        'reflectivity': 'reflectivity',  # need to change to input_reflectivity
        'velocity': 'mean_doppler_velocity',
        'normalized_coherent_power': 'normalized_coherent_power',
        'cross_correlation_ratio': 'cross_correlation_ratio_hv',
        'input_phidp_field': 'differential_phase',
        'input_clutter_corrected_reflectivity': 'reflectivity',
        'clutter': 'ground_clutter',
        'differential_reflectivity': 'differential_reflectivity',
        'signal_to_noise_ratio': None,
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',  # output phidp, need to change
        'refl_field': 'corrected_reflectivity'},  # output Z field
    
    # SAIL X-band radar names
    'sail_xband_ppi': {
        'input_zdr': 'ZDR',
        'reflectivity': 'DBZ',
        'normalized_coherent_power': 'NCP',
        'cross_correlation_ratio': 'RHOHV',
        'input_phidp_field': 'PHIDP',
        'input_clutter_corrected_reflectivity': 'DBZ',
        'velocity': 'VEL',
        'differential_reflectivity': 'ZDR',
        'signal_to_noise_ratio': 'SNR',
        'clutter': 'ground_clutter',
        # Sonde field names
        'altitude': 'alt',
        'temperature': 'tdry',
        'u_wind': 'u_wind',
        'v_wind': 'v_wind',
        # Input field names to attenuation code
        'zdr_field': 'corrected_differential_reflectivity',
        'pia_field': 'path_integrated_attenuation',
        'phidp_field': 'filtered_corrected_differential_phase',  # output phidp, need to change
        'refl_field': 'corrected_reflectivity'},  # output Z field
}

##############################################################################
# Membership functions
#
# This goes into the following section cmac_config
##############################################################################

# csapr2_cordoba
cacti_csapr2_ppi_mbfs={'multi_trip': {'velocity_texture': [[7.7, 10.0, 130.0, 130.0], 4.0],
                                 'copol_correlation_coeff': [[0.7, 0.8, 1, 1], 0.0],
                                 'normalized_coherent_power': [[0, 0, 0.3, 0.35], 1.0],
                                 'height': [[0, 0, 5000, 8000], 0.0],
                                 'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                                 'signal_to_noise_ratio': [[20, 22, 1000, 1000], 1.0]},
                  'rain': {'velocity_texture': [[0, 0, 2.4, 2.5], 1.0],
                           'copol_correlation_coeff': [[0.97, 0.98, 1, 1], 1.0],
                           'normalized_coherent_power': [[0.4, 0.5, 1, 1], 1.0],
                           'height': [[0, 0, 5000, 6000], 0.0],
                           'sounding_temperature': [[2.0, 5.0, 100, 100], 2.0],
                           'signal_to_noise_ratio': [[20, 22, 1000, 1000], 1.0]},
                  'snow': {'velocity_texture': [[0, 0, 2.4, 2.5], 1.0],
                           'copol_correlation_coeff': [[0.65, 0.9, 1, 1], 1.0],
                           'normalized_coherent_power': [[0.4, 0.5, 1, 1], 1.0],
                           'height': [[0, 0, 25000, 25000], 0.0],
                           'sounding_temperature': [[-100, -100, 0.5, 4.0], 2.0],
                           'signal_to_noise_ratio': [[20, 22, 1000, 1000], 1.0]},
                  'no_scatter': {'velocity_texture': [[0, 0, 330.0, 330.0], 2.0],
                                 'copol_correlation_coeff': [[0, 0, 0.1, 0.2], 0.0],
                                 'normalized_coherent_power': [[0, 0, 0.1, 0.2], 0.0],
                                 'height': [[0, 0, 25000, 25000], 0.0],
                                 'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                                 'signal_to_noise_ratio': [[-100, -100, 20, 22], 4.0]},
                'melting': {'velocity_texture': [[0, 0, 2.4, 2.5], 0.0],
                            'copol_correlation_coeff': [[0.6, 0.65, 0.9, 0.96], 2.0],
                            'normalized_coherent_power': [[0.4, 0.5, 1, 1], 0],
                            'height': [[0, 0, 25000, 25000], 0.0],
                            'sounding_temperature': [[0, 0.1, 2, 4], 4.0],
                            'signal_to_noise_ratio': [[20, 22, 1000, 1000], 0.0]}}

# csapr2_bnf
bnf_csapr2_ppi_mbfs={'multi_trip': {'velocity_texture': [[7.7, 10.0, 130.0, 130.0], 4.0],
                                 'copol_correlation_coeff': [[0.7, 0.8, 1, 1], 0.0],
                                 'normalized_coherent_power': [[0, 0, 0.3, 0.35], 1.0],
                                 'height': [[0, 0, 5000, 8000], 0.0],
                                 'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                                 'signal_to_noise_ratio': [[-2, 2, 1000, 1000], 1.0]},
                  'rain': {'velocity_texture': [[0, 0, 2.0, 2.1], 0.0],
                           'copol_correlation_coeff': [[0.97, 0.98, 1, 1], 2.0],
                           'normalized_coherent_power': [[0.4, 0.5, 1, 1], 0.0],
                           'height': [[0, 0, 5000, 6000], 0.0],
                           'sounding_temperature': [[2.0, 5.0, 100, 100], 2.0],
                           'signal_to_noise_ratio': [[-2, 2, 1000, 1000], 1.0]},
                  'snow': {'velocity_texture': [[0, 0, 2.0, 2.1], 1.0],
                           'copol_correlation_coeff': [[0.85, 0.9, 1, 1], 1.0],
                           'normalized_coherent_power': [[0.4, 0.5, 1, 1], 1.0],
                           'height': [[0, 0, 25000, 25000], 0.0],
                           'sounding_temperature': [[-100, -100, 0.5, 4.0], 2.0],
                           'signal_to_noise_ratio': [[-2, 2, 1000, 1000], 1.0]},
                  'no_scatter': {'velocity_texture': [[0, 0, 330.0, 330.0], 2.0],
                                 'copol_correlation_coeff': [[0, 0, 0.1, 0.2], 0.0],
                                 'normalized_coherent_power': [[0, 0, 0.1, 0.2], 0.0],
                                 'height': [[0, 0, 25000, 25000], 0.0],
                                 'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                                 'signal_to_noise_ratio': [[-100, -100, -2, 0], 4.0]},
                'melting': {'velocity_texture': [[0, 0, 2.0, 2.1], 0.0],
                            'copol_correlation_coeff': [[0.6, 0.65, 0.95, 0.96], 4.0],
                            'normalized_coherent_power': [[0.4, 0.5, 1, 1], 0],
                            'height': [[0, 0, 25000, 25000], 0.0],
                            'sounding_temperature': [[-1, -0.5, 3, 4], 4.0],
                            'signal_to_noise_ratio': [[-2, 2, 1000, 1000], 0.0]}}

cacti_csapr2_ppi_hard_const = [['melting', 'sounding_temperature', (10, 100)],
                               ['multi_trip', 'height', (10000, 1000000)],
                               ['melting', 'sounding_temperature', (-10000, -2)],
                               ['rain', 'sounding_temperature', (-1000, -5)],
                               ['snow', 'sounding_temperature', (3, 100)],
                               ['melting', 'velocity_texture', (3, 300)]]

# NSA X-SAPR Fuzzy Values.
nsa_xsapr_ppi_mbfs={'multi_trip': {
                        'velocity_texture': [[2.0, 2.1, 130., 130.], 4.0],
                        'cross_correlation_ratio_hv': [[.5, .7, 1, 1], 0.0],
                        'normalized_coherent_power': [[0, 0, .5, .6], 1.0],
                        'height': [[0, 0, 5000, 8000], 0.0],
                        'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                        'signal_to_noise_ratio': [[5, 10, 1000, 1000], 1.0]},

                    'rain': {
                        'velocity_texture': [[0, 0, 2.0, 2.1], 1.0],
                        'cross_correlation_ratio_hv': [[0.97, 0.98, 1, 1], 1.0],
                        'normalized_coherent_power': [[0.4, 0.5, 1, 1], 1.0],
                        'height': [[0, 0, 5000, 6000], 0.0],
                        'sounding_temperature': [[2., 5., 100, 100], 2.0],
                        'signal_to_noise_ratio': [[8, 10, 1000, 1000], 1.0]},

                    'snow': {
                        'velocity_texture': [[0, 0, 2.0, 2.1], 1.0],
                        'cross_correlation_ratio_hv': [[0.65, 0.9, 1, 1], 1.0],
                        'normalized_coherent_power': [[0.4, 0.5, 1, 1], 1.0],
                        'height': [[0, 0, 25000, 25000], 0.0],
                        'sounding_temperature': [[-100, -100, .5, 4.], 2.0],
                        'signal_to_noise_ratio': [[8, 10, 1000, 1000], 1.0]},

                    'no_scatter': {
                        'velocity_texture': [[2.0, 2.1, 330., 330.], 2.0],
                        'cross_correlation_ratio_hv': [[0, 0, 0.1, 0.2], 0.0],
                        'normalized_coherent_power': [[0, 0, 0.1, 0.2], 0.0],
                        'height': [[0, 0, 25000, 25000], 0.0],
                        'sounding_temperature': [[-100, -100, 100, 100], 0.0],
                        'signal_to_noise_ratio': [[-100, -100, 5, 10], 4.0]},

                    'melting': {
                        'velocity_texture': [[0, 0, 2.0, 2.1], 0.0],
                        'cross_correlation_ratio_hv': [[0.6, 0.65, .9, .96], 2.0],
                        'normalized_coherent_power': [[0.4, 0.5, 1, 1], 0],
                        'height': [[0, 0, 25000, 25000], 0.0],
                        'sounding_temperature': [[0, 0.1, 2, 4], 4.0],
                        'signal_to_noise_ratio': [[8, 10, 1000, 1000], 0.0]}}


nsa_xsapr_ppi_hard_const = [['melting', 'sounding_temperature', (10, 100)],
                            ['multi_trip', 'height', (10000, 1000000)],
                            ['melting', 'sounding_temperature', (-10000, -2)],
                            ['rain', 'sounding_temperature', (-1000, -5)],
                            ['melting', 'velocity_texture', (3, 300)]]



##############################################################################
# Default CMAC values
#
# The DEFAULT_CMAC_VALUES dictionary contains dictionaries for radars that
# contains parameter values used in the CMAC processing. Values in these
# radar dictionaries are used for a variety of functions, such as hydrometeor
# classification, phase processing, specific attenuation and more. These
# values are all used within cmac_radar.py.
##############################################################################

_DEFAULT_CMAC_VALUES = {
    # X-SAPR I6 PPI CMAC processing values.
    'xsapr_i6_ppi': {
        'save_name': 'sgpxsaprcmacsurI6.c1',
        'sonde_name': 'sgpsondewnpnC1.b1',
        'x_compass': 'XNW',
        'site_alt': 341,
        'ref_offset': 0.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1,
        'beta_coef': 1,
        'zdr_offset': 3.05,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,},

    # X-SAPR I5 PPI CMAC processing values.
    'xsapr_i5_cfr_ppi': {
        'save_name': 'sgpxsaprcmacsurI5.c1',
        'sonde_name': 'sgpsondewnpnC1.b1',
        'x_compass': 'XSW',
        'site_alt': 328,
        'ref_offset': 0.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,},

    # X-SAPR I4 PPI CMAC processing values.
    'xsapr_i4_ppi': {
        'save_name': 'sgpxsaprcmacsurI4.c1',
        'sonde_name': 'sgpsondewnpnC1.b1',
        'x_compass': 'XSE',
        'site_alt': 330,
        'ref_offset': 0.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1,
        'beta_coef': 1,
        'zdr_offset': 3.05,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,},

    # X-SAPR I6 Sector CMAC processing values.
    'xsapr_i6_sec': {
        'save_name': 'sgpxsaprcmacsecI6.c1',
        'sonde_name': 'sgpsondewnpnC1.b1',
        'x_compass': 'XNW',
        'site_alt': 341,
        'ref_offset': 0.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1,
        'beta_coef': 1,
        'zdr_offset': 3.05,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,},

    # X-SAPR I5 Sector CMAC processing values.
    'xsapr_i5_sec': {
        'save_name': 'sgpxsaprcmacsecI5.c1',
        'sonde_name': 'sgpsondewnpnC1.b1',
        'x_compass': 'XSW',
        'site_alt': 328,
        'ref_offset': 0.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1,
        'beta_coef': 1,
        'zdr_offset': 3.05,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,},

    # X-SAPR I5 Sector CMAC processing values.
    'xsapr_i5_ppi': {
        'save_name': 'sgpxsaprcmacsecI5.c1',
        'sonde_name': 'sgpsondewnpnC1.b1',
        'x_compass': 'XSW',
        'site_alt': 328,
        'ref_offset': 0.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1,
        'beta_coef': 1,
        'zdr_offset': 3.05,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,},
    
    # X-SAPR I5 RHI CMAC processing values.
    'xsapr_i5_rhi': {
        'save_name': 'sgpxsaprcmacrhiI5.c1',
        'sonde_name': 'sgpsondewnpnC1.b1',
        'x_compass': 'XSW',
        'site_alt': 328,
        'ref_offset': 0.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1,
        'beta_coef': 1,
        'zdr_offset': 3.05,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,},

    # X-SAPR I4 Sector CMAC processing values.
    'xsapr_i4_sec': {
        'save_name': 'sgpxsaprcmacsecI4.c1',
        'sonde_name': 'sgpsondewnpnC1.b1',
        'x_compass': 'XSE',
        'site_alt': 330,
        'ref_offset': 0.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1,
        'beta_coef': 1,
        'zdr_offset': 3.05,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,},

    # CACTI C-SAPR 2 CMAC processing values.
    'cacti_csapr2_ppi': {
        'save_name': 'corcsapr2cmacppi.c1',
        'sonde_name': 'corsondewnpnM1.b1',
        'site_alt': 1141,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.08,
        'c_coef': 0.3,
        'd_coef': 1.804,
        'beta_coef': 0.64884,  # ZDR corrections
        'flip_phidp': True,
        'phidp_flipped': ['uncorrected_differential_phase','differential_phase'],
        'mbfs': cacti_csapr2_ppi_mbfs,
        'hard_const': cacti_csapr2_ppi_hard_const,
        'gen_clutter_from_refl': True,
        'ref_offset': 0.0,
        'gen_clutter_from_refl_diff': -0.2,
        'gen_clutter_from_refl_alt': 2000.0,
        'clutter_mask_z_for_texture': True,
        'rain_rate_a_coef_A': 294.0,
        'rain_rate_b_coef_A': 0.89,
        'rain_rate_a_coef_A': 294.0,
        'rain_rate_b_coef_A': 0.89,
        'rain_rate_a_coef_Z': 0.017,
        'rain_rate_b_coef_Z': 0.714,
        'rain_rate_a_coef_Kdp': 25.1,
        'rain_rate_b_coef_Kdp': 0.777,
        'beam_width': 1.0,
        'radar_height_offset': 10.0,},  # We expect clutter corrected fields now
    
    # Tracer C-SAPR 2 CMAC processing values.
    'tracer_csapr2_ppi': {
        'save_name': 'houcsapr2cmacppiS2.c1',
        'sonde_name': 'housondewnpnM1.b1',
        'site_alt': 12,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.08,
        'c_coef': 0.3,
        'd_coef': 1.804,
        'beta_coef': 0.64884,  # ZDR corrections
        'flip_phidp': True,
        'phidp_flipped': ['uncorrected_differential_phase','differential_phase'],
        'mbfs': cacti_csapr2_ppi_mbfs,
        'hard_const': cacti_csapr2_ppi_hard_const,
        'gen_clutter_from_refl': True,
        'ref_offset': 0.0,
        'gen_clutter_from_refl_diff': -0.2,
        'gen_clutter_from_refl_alt': 2000.0,
        'clutter_mask_z_for_texture': True,
        'rain_rate_a_coef_A': 294.0,
        'rain_rate_b_coef_A': 0.89,
        'rain_rate_a_coef_Z': 0.017,
        'rain_rate_b_coef_Z': 0.714,
        'rain_rate_a_coef_Kdp': 25.1,
        'rain_rate_b_coef_Kdp': 0.777,
        'beam_width': 1.0,
        'radar_height_offset': 10.0,},  # We expect clutter corrected fields now

    # Tracer C-SAPR 2 CMAC processing values.
    'bnf_csapr2_ppi': {
        'save_name': 'bnfcsapr2cmacppiS3.c1',
        'sonde_name': 'bnfsondewnpnM1.b1',
        'site_alt': 12,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.0633,
        'c_coef': 0.3,
        'd_coef': 1.0804,
        'beta_coef': 0.64884,  # ZDR corrections
        'flip_phidp': False,
        'phidp_flipped': ['uncorrected_differential_phase','differential_phase'],
        'mbfs': bnf_csapr2_ppi_mbfs,
        'hard_const': cacti_csapr2_ppi_hard_const,
        'gen_clutter_from_refl': False,
        'ref_offset': 0.8,
        'zdr_offset': 0.7,
        'gen_clutter_from_refl_diff': -0.2,
        'gen_clutter_from_refl_alt': 2000.0,
        'clutter_mask_z_for_texture': False,
        'rain_rate_a_coef_A': 294.0,
        'rain_rate_b_coef_A': 0.89,
        'rain_rate_a_coef_Z': 0.017,
        'rain_rate_b_coef_Z': 0.714,
        'rain_rate_a_coef_Kdp': 25.1,
        'rain_rate_b_coef_Kdp': 0.777,
        'kdp_method': "bringi",
        # PhiDP system phase offset in degrees. None estimates it from
        # each volume; set a number to pin it.
        'phidp_sys_phase': None,
        'beam_width': 1.0,
        'radar_height_offset': 10.0,},  # We expect clutter corrected fields now

    # NSA X-SAPR CMAC processing values.
    'nsa_xsapr_ppi': {
        'save_name': 'nsaxsaprcmacppiC1.c1',
        'sonde_name': 'nsasondewnpnC1.b1',
        'site_alt': 17.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1.0,
        'beta_coef': 0.64884,  # ZDR corrections
        'flip_phidp': False,
        'phidp_flipped': ['uncorrected_differential_phase','differential_phase'],
        'mbfs': nsa_xsapr_ppi_mbfs,
        'hard_const': nsa_xsapr_ppi_hard_const,
        'gen_clutter_from_refl': False,
        'ref_offset': 0.0,
        'gen_clutter_from_refl_diff': -0.2,
        'gen_clutter_from_refl_alt': 2000.0,
        'clutter_mask_z_for_texture': True,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801,
        'beam_width': 1.0,
        'radar_height_offset': 10.0,},
    
    # X-SAPR I4 Sector CMAC processing values.
    'sail_xband_ppi': {
        'save_name': 'gucxprecipradarcmacppiS2.c1',
        'sonde_name': 'gucsondewnpnM1.b1',
        'x_compass': 'XSE',
        'site_alt': 3149.19995117,
        'ref_offset': 2.0,
        'self_const': 60000.00,
        'attenuation_a_coef': 0.17,
        'c_coef': 0.05,
        'd_coef': 1,
        'beta_coef': 1,
        'zdr_offset': 0.5,
        'rain_rate_a_coef_A': 43.5,
        'rain_rate_b_coef_A': 0.79,
        'rain_rate_a_coef_Z': 0.029,
        'rain_rate_b_coef_Z': 0.67,
        'rain_rate_a_coef_Kdp': 16.9,
        'rain_rate_b_coef_Kdp': 0.801},

}


##############################################################################
# Default plot values
#
# The DEFAULT_PLOT_VALUES dictionary contains dictionaries for radars that
# contains parameter values used in the CMAC quicklooks. Values in these
# radar dictionaries are used for defining specifications for plotting
# specific radars. Specifications such as, max latitude and longitude, sweep
# and coordinates for dual doppler lobes. These values are all used within
# cmac_quicklooks.py.
##############################################################################

_DEFAULT_PLOT_VALUES = {
    # X-SAPR I6 PPI plot values.
    'xsapr_i6_ppi': {
        'save_name': 'sgpxsaprcmacsurI6.c1',
        'facility': 'I6',
        'sweep': 3,
        'max_lat': 37.3,
        'min_lat': 36.25,
        'max_lon': -96.9,
        'min_lon': -98.2,
        'site_i6_dms_lat': (36, 46, 2.28),
        'site_i6_dms_lon': (-97, 32, 53.16),
        'site_i5_dms_lat': (36, 29, 29.4),
        'site_i5_dms_lon': (-97, 35, 37.68),
        'site_i4_dms_lat': (36, 34, 44.4),
        'site_i4_dms_lon': (-97, 21, 49.32)},

    # X-SAPR I5 PPI plot values.
    'xsapr_i5_ppi': {
        'save_name': 'sgpxsaprcmacsurI5.c1',
        'facility': 'I5',
        'sweep': 3,
        'max_lat': 37.0,
        'min_lat': 36.0,
        'max_lon': -97.0,
        'min_lon': -98.3,
        'site_i6_dms_lat': (36, 46, 2.28),
        'site_i6_dms_lon': (-97, 32, 53.16),
        'site_i5_dms_lat': (36, 29, 29.4),
        'site_i5_dms_lon': (-97, 35, 37.68),
        'site_i4_dms_lat': (36, 34, 44.4),
        'site_i4_dms_lon': (-97, 21, 49.32)},
    
    # X-SAPR I5 PPI plot values.
    'xsapr_i5_cfr_ppi': {
        'save_name': 'sgpxsaprcmacsurI5.c1',
        'facility': 'I5',
        'sweep': 3,
        'max_lat': 37.0,
        'min_lat': 36.0,
        'max_lon': -97.0,
        'min_lon': -98.3,
        'site_i6_dms_lat': (36, 46, 2.28),
        'site_i6_dms_lon': (-97, 32, 53.16),
        'site_i5_dms_lat': (36, 29, 29.4),
        'site_i5_dms_lon': (-97, 35, 37.68),
        'site_i4_dms_lat': (36, 34, 44.4),
        'site_i4_dms_lon': (-97, 21, 49.32)},

    # X-SAPR I4 PPI plot values.
    'xsapr_i4_ppi': {
        'save_name': 'sgpxsaprcmacsurI4.c1',
        'facility': 'I4',
        'sweep': 3,
        'max_lat': 37.1,
        'min_lat': 36.1,
        'max_lon': -96.7,
        'min_lon': -98.0,
        'site_i6_dms_lat': (36, 46, 2.28),
        'site_i6_dms_lon': (-97, 32, 53.16),
        'site_i5_dms_lat': (36, 29, 29.4),
        'site_i5_dms_lon': (-97, 35, 37.68),
        'site_i4_dms_lat': (36, 34, 44.4),
        'site_i4_dms_lon': (-97, 21, 49.32)},

    # X-SAPR I6 Sector plot values.
    'xsapr_i6_sec': {
        'save_name': 'sgpxsaprcmacsecI6.c1',
        'facility': 'I6',
        'sweep': 1,
        'max_lat': 36.85,
        'min_lat': 35.8,
        'max_lon': -96.5,
        'min_lon': -98.15,
        'site_i6_dms_lat': (36, 46, 2.28),
        'site_i6_dms_lon': (-97, 32, 53.16),
        'site_i5_dms_lat': (36, 29, 29.4),
        'site_i5_dms_lon': (-97, 35, 37.68),
        'site_i4_dms_lat': (36, 34, 44.4),
        'site_i4_dms_lon': (-97, 21, 49.32)},

    # X-SAPR I5 Sector plot values.
    'xsapr_i5_sec': {
        'save_name': 'sgpxsaprcmacsecI5.c1',
        'facility': 'I5',
        'sweep': 1,
        'max_lat': 37.4,
        'min_lat': 36.49,
        'max_lon': -96.45,
        'min_lon': -97.8,
        'site_i6_dms_lat': (36, 46, 2.28),
        'site_i6_dms_lon': (-97, 32, 53.16),
        'site_i5_dms_lat': (36, 29, 29.4),
        'site_i5_dms_lon': (-97, 35, 37.68),
        'site_i4_dms_lat': (36, 34, 44.4),
        'site_i4_dms_lon': (-97, 21, 49.32)},

    # X-SAPR I4 Sector plot values.
    'xsapr_i4_sec': {
        'save_name': 'sgpxsaprcmacsecI4.c1',
        'facility': 'I4',
        'sweep': 1,
        'max_lat': 37.4,
        'min_lat': 36.05,
        'max_lon': -97.3,
        'min_lon': -98.6,
        'site_i6_dms_lat': (36, 46, 2.28),
        'site_i6_dms_lon': (-97, 32, 53.16),
        'site_i5_dms_lat': (36, 29, 29.4),
        'site_i5_dms_lon': (-97, 35, 37.68),
        'site_i4_dms_lat': (36, 34, 44.4),
        'site_i4_dms_lon': (-97, 21, 49.32)},

    # CACTI C-SAPR 2 plot values.
    'cacti_csapr2_ppi': {
        'save_name': 'cacticsaprcmacppi.c1',
        'sweep': 3},
  
    # CACTI C-SAPR 2 plot values.
    'tracer_csapr2_ppi': {
        'save_name': 'houcsaprcmacppiS2.c1',
        'sweep': 3},
    
    # CACTI C-SAPR 2 plot values.
    'bnf_csapr2_rhi': {
        'save_name': 'bnfcsaprcmacrhiS3.c1',
        'sweep': 0},

    # CACTI C-SAPR 2 plot values.
    'bnf_csapr2_ppi': {
        'save_name': 'bnfcsaprcmacppiS2.c1',
        'min_lat': 33.7,
        'max_lat': 35.65,
        'min_lon': -88.4,
        'max_lon': -85.9,
        'sweep': 0},

    # CACTI C-SAPR 2 plot values.
    'xsapr_i5_rhi': {
        'save_name': 'sgpxsaprcmacrhiI5.c1',
        'sweep': 0},

    # NSA X-SAPR plot values.
    'nsa_xsapr_ppi': {
        'save_name': 'nsaxsaprcmacppi.c1',
        'sweep': 3},
    
    # NSA X-SAPR plot values.
    'sail_xband_ppi': {
        'save_name': 'gucxprecipcmacppi.c1',
        'facility': 'S2',
        'sweep': 3},
}

#########################################################################
# Z-S relationships for snowfall rates
#
# This dictionary contains the coefficients to the relationship Z = AS^B
# for given Z-S relationships. The keys to this dictionary are the long
# name of the relationship. Each dictionary member is a dictionary 
# containing the A coefficient (A), B coefficient (B), and abbreviation
# used for the variable name (abbreviation).
#
#########################################################################

_DEFAULT_ZS_RELATIONSHIPS = {"Wolf and Snider (2012)":
                            {"A": 110,
                             "B": 2,
                             "abbreviation": 'ws2012'},
                              "WSR 88D High Plains":
                             {"A": 40,
                              "B": 2,
                              "abbreviation": 'ws88diw'},
                              "Matrosov et al.(2009) Braham(1990) 1":
                              {"A": 67,
                              "B": 1.28,
                              "abbreviation": "m2009_1"},
                              "Matrosov et al.(2009) Braham(1990) 2":
                              {"A": 114,
                              "B": 1.39,
                              "abbreviation": "m2009_2"},
                             }


#########################################################################
# Default global metadata fallback used by ``cmac()`` when the caller
# does not pass ``meta_append``. Overridable via the top-level
# ``default_metadata`` YAML section.
#########################################################################

_DEFAULT_GLOBAL_METADATA = {
    'data_level': 'sgp',
    'comment': 'This is highly experimental and initial data. '
               + 'There are many known and unknown issues. Please do '
               + 'not use before contacting the Translator responsible '
               + 'scollis@anl.gov',
    'attributions': 'This data is collected by the ARM Climate Research '
                    + 'facility. Radar system is operated by the radar '
                    + 'engineering team radar@arm.gov and the data is '
                    + 'processed by the precipitation radar products '
                    + 'team. LP code courtesy of Scott Giangrande, BNL.',
    'version': '2.0 lite',
    'vap_name': 'cmac',
    'known_issues': 'False phidp jumps in insect regions. Still uses '
                    + 'old Giangrande code.',
    'developers': 'Robert Jackson, ANL. Zachary Sherman, ANL.',
    'translator': 'Scott Collis, ANL.',
    'mentors': 'Bradley Isom, PNNL., Iosif Lindenmaier, PNNL.',
    'Conventions': 'CF/Radial instrument_parameters ARM-1.3'}


#########################################################################
# Default processing tunables and plot-field ranges
#
# These dictionaries hold the literal numeric defaults previously baked
# into ``cmac_radar.py``, ``cmac_processing.py``, and the quicklooks
# modules. Per-radar entries in ``_DEFAULT_CMAC_VALUES`` and
# ``_DEFAULT_PLOT_VALUES`` are populated from these dictionaries below;
# users can override any single value via the YAML config.
#########################################################################

# Processing tunables (cmac_radar.py / cmac_processing.py)
_DEFAULT_PROCESSING_TUNABLES = {
    'snow_density': 0.073,
    'phidp_nowrap': 50,
    'kdp_phase_proc_max': 10.0,
    'phidp_despeckle_size': 49,
    'corrected_velocity_valid_min': -100.0,
    'corrected_velocity_valid_max': 100.0,
    'melt_fzl_ceiling': 5000.0,
    'melt_fzl_replacement': 3500.0,
    'melt_fzl_floor': 1000.0,
    'max_kdp': 15.0,
    'velocity_texture_window': 4,
    'velocity_texture_median_size': (4, 4),
    'fuzzy_score_median_size': (3, 4),
    'fuzzy_tex_start': 2.0,
    'fuzzy_tex_end': 2.1,
    'area_coverage_precip_threshold': 10.0,
    'area_coverage_convection_threshold': 40.0,
    'rain_rate_valid_max': 400,
    'snow_rate_valid_max': 500,
    'cbb_blockage_threshold': 0.80,
    # Whether a vendor classification_mask field, when present, is allowed to
    # relabel gates as clutter. True preserves the behaviour this overlay has
    # always had. Set it false where the mask's clutter bit is set at
    # essentially every gate, which is the case on TRACER C-SAPR2 a1 volumes
    # and turns the whole volume into clutter; see cmac_radar.cmac.
    'use_classification_mask': True,
    # Which classifier fills the gate_id field. 'cmac_fuzzy' is CMAC's own
    # five-class fuzzy scheme (cmac_processing.do_my_fuzz) and is the default
    # everywhere, so behaviour is unchanged unless a config asks otherwise.
    # 'radar_palette' delegates to radar_palette.gateid's eleven-class
    # classifier and folds the result onto the same five categories, keeping
    # the full class set in the scatterer_classification field. See
    # cmac.gate_id_backends.
    'gate_id_method': 'cmac_fuzzy',
    # The remaining gate_id_* keys are read only by the radar_palette backend.
    # Each of the tuning knobs left as None takes that classifier's own
    # documented default, so a value is pinned here only where CMAC has a
    # reason to differ.
    #
    # Class name -> CMAC category, overriding
    # gate_id_backends.RADAR_PALETTE_TO_CMAC for the classes named. Partial
    # maps are merged over the default, so only the classes being rerouted
    # need listing.
    'gate_id_class_map': None,
    # Freezing level in m MSL handed to the classifier's melting-layer
    # constraints. None derives it from the mapped sounding, which is what a
    # site with a sounding should use; pin a number only when the sounding is
    # known to be unrepresentative.
    'gate_id_freezing_level': None,
    # Classification runs on the uncorrected moments where the volume
    # publishes them (see gate_id_backends.UNCORRECTED_CANDIDATES). Those have
    # not been through the in-place ref_offset/zdr_offset that cmac() applies
    # to the configured fields, so the offsets are added to the classifier's
    # view of them. Set false to classify on the raw instrument values.
    'gate_id_apply_offsets': True,
    # What to do when radar_palette declines to classify a volume -- it skips
    # sweeps it judges unsuitable (a narrow-elevation-span RHI, for instance)
    # and returns 'unclassified' for every gate in them, which folds to
    # no_scatter and is then indistinguishable from clear air. 'warn' reports
    # it and continues; 'error' makes it a hard failure, which is what a
    # production run that must not emit an empty mask should use.
    'gate_id_unclassified_policy': 'warn',
    'gate_id_snr_min': 3.0,
    'gate_id_min_run': 3,
    'gate_id_despeckle_keep_dbz': 30.0,
    # Velocity texture, as a fraction of the uniform-random-phase limit, above
    # which a gate cannot be first-trip weather. Measured to be
    # instrument-specific rather than universal, so it is exposed per radar;
    # 0 disables the test, None takes radar_palette's own constant.
    'gate_id_incoherent_frac': None,
    'gate_id_texture_window': 4,
    # The winning-minus-runner-up score is a useful diagnostic but doubles the
    # classification storage in the output file, so publishing it is opt-in.
    'gate_id_publish_margin': False,
}

# Plot-field vmin/vmax pairs used by the quicklooks
_DEFAULT_PLOT_FIELD_RANGES = {
    'reflectivity_raw_vmin': -8,
    'reflectivity_raw_vmax': 64,
    'reflectivity_vmin': -8,
    'reflectivity_vmax': 40,
    'velocity_texture_vmin': 0,
    'velocity_texture_vmax': 14,
    'cross_correlation_ratio_vmin': 0.5,
    'cross_correlation_ratio_vmax': 1.0,
    'specific_attenuation_vmin': 0,
    'specific_attenuation_vmax': 1.0,
    'corrected_specific_diff_phase_vmin': 0,
    'corrected_specific_diff_phase_vmax': 6,
    'filtered_corrected_differential_phase_vmin': 0,
    'filtered_corrected_differential_phase_vmax': 360,
    'filtered_corrected_specific_diff_phase_vmin': -2,
    'filtered_corrected_specific_diff_phase_vmax': 10,
    'corrected_reflectivity_vmin': 0,
    'corrected_reflectivity_vmax': 40,
    'corrected_velocity_vmin': -60,
    'corrected_velocity_vmax': 60,
    'rain_rate_vmin': 0,
    'rain_rate_vmax': 120,
    'snow_rate_vmin': 0,
    'snow_rate_vmax': 50,
}

# Layout / misc plotting defaults
_DEFAULT_PLOT_LAYOUT = {
    'figsize_single': [12, 8],
    'figsize_panel': [15, 10],
    'lat_lon_tick_spacing': 0.8,
    'dd_lobe_grid_spacing': 0.01,
    'dd_lobe_bca_levels': [0.5235987755982988, 2.6179938779914944],  # [pi/6, 5*pi/6]
    'sweep_fallback_nsweeps_lt': 4,
    'sweep_fallback': 2,
    'ymin': 0,
    'ymax': 10,
    'cat_colors': {
        'rain': 'green',
        'multi_trip': 'red',
        'no_scatter': 'gray',
        'snow': 'cyan',
        'melting': 'yellow',
        'clutter': 'black',
        'terrain_blockage': 'brown',
    },
}

# Helpers used below to attach the new defaults to every per-radar entry
# without losing any existing per-radar overrides.

def _with_processing_defaults(radar_cfg):
    merged = dict(_DEFAULT_PROCESSING_TUNABLES)
    merged.update(radar_cfg)
    return merged


def _with_plot_defaults(radar_cfg):
    merged = dict(_DEFAULT_PLOT_FIELD_RANGES)
    merged.update(_DEFAULT_PLOT_LAYOUT)
    merged.update(radar_cfg)
    return merged


_DEFAULT_CMAC_VALUES = {
    radar: _with_processing_defaults(cfg)
    for radar, cfg in _DEFAULT_CMAC_VALUES.items()
}

_DEFAULT_PLOT_VALUES = {
    radar: _with_plot_defaults(cfg)
    for radar, cfg in _DEFAULT_PLOT_VALUES.items()
}


