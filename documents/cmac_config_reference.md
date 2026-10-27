# CMAC YAML Configuration Reference

CMAC needs, per radar, a set of field-name mappings, processing thresholds,
plot ranges, and output metadata. The built-in values for every radar CMAC
already knows about live in `cmac/default_config.py`. To process a radar
that isn't in there — or to tweak a couple of values for one that is —
write a YAML file and pass its path as `config_file=` instead of editing
the Python defaults.

Two worked examples ship in the repository:

- `documents/example_config.yaml` — a minimal file showing how to override
  one existing radar and add a brand-new one.
- `configs/bnfcsapr2.yaml` — a complete, real configuration (both PPI and
  RHI scan strategies) for the BNF C-SAPR2 radar.

## Where a config file is accepted

Every function that reads per-radar configuration takes an optional
`config_file` argument:

- `cmac.cmac(radar, sonde, config, config_file=...)`
- `cmac.quicklooks_ppi(radar, config, config_file=...)` /
  `cmac.quicklooks_rhi(radar, config, config_file=...)`
- `cmac.area_coverage(radar, config=..., config_file=...)`
- `cmac.tall_clutter(..., config_file=...)`
- The lower-level getters in `cmac.config`: `get_metadata`,
  `get_field_names`, `get_cmac_values`, `get_plot_values`,
  `get_zs_relationships`, `get_default_metadata`

as well as the `cmac` command line script, via `-c` / `--config-file`.

`config` (the other required argument, e.g. `"bnf_csapr2_ppi"`) selects
*which* radar's entry to use out of the file/defaults. It must match a key
under the relevant section, either in `cmac/default_config.py` or in your
YAML file.

## Merge semantics

Loading is per-radar-key and per-section, not whole-file:

1. Start from `cmac/default_config.py`'s dict for `config` in that section
   (empty dict if `config` isn't a built-in radar).
2. If a YAML file was given and it defines that same section + `config`
   key, its keys are merged on top, overriding matching keys and adding
   new ones.
3. Everything you don't mention keeps its default value.

This means you only ever need to list the handful of values you actually
want to change — you never have to restate an entire radar's configuration
to override one threshold. The one exception is `mbfs` (see below): setting
it in YAML replaces the whole fuzzy-logic membership-function dict, not
just the classes you list.

Requires `PyYAML` (`pip install pyyaml`).

## Top-level structure

All five sections are optional — include only what you need.

```yaml
metadata:
  <config_name>:
    <key>: <value>
    ...

field_names:
  <config_name>:
    <key>: <value>
    ...

cmac_values:
  <config_name>:
    <key>: <value>
    ...

plot_values:
  <config_name>:
    <key>: <value>
    ...

zs_relationships:
  <relationship name>:
    A: <float>
    B: <float>
    abbreviation: <str>

default_metadata:
  <key>: <value>
  ...
```

`<config_name>` is the same string passed as `config` everywhere else,
e.g. `bnf_csapr2_ppi`. `default_metadata` is not per-radar — it's the
single global fallback used by `cmac()` when `meta_append` is `None` or
`"default"` (see [Metadata](#metadata-and-default_metadata) below).

### Adding a brand-new radar

If `config_name` isn't already a key in `cmac/default_config.py`, you must
supply every section the functions you call actually read:

| You call... | Sections required for that `config_name` |
|---|---|
| `cmac()` | `field_names`, `cmac_values`, `metadata` |
| `quicklooks_ppi()` / `quicklooks_rhi()` | `field_names`, `plot_values` |
| `area_coverage(config=...)` | `cmac_values` (only for its two threshold keys; both have hard-coded fallbacks otherwise) |

Missing a required section for a config name not covered by the defaults
raises `KeyError`.

### YAML anchors for near-duplicate radars

`bnf_csapr2_ppi` and `bnf_csapr2_rhi` describe the same physical radar with
two scan strategies, so `configs/bnfcsapr2.yaml` defines `metadata`,
`field_names`, and `cmac_values` once with a YAML anchor (`&name`) and
reuses them for the second key with a merge key (`<<: *name`), overriding
only what actually differs (typically `save_name`):

```yaml
cmac_values:
  bnf_csapr2_ppi: &bnf_csapr2_cmac_values
    save_name: bnfcsapr2cmacppiS3.c1
    ...
  bnf_csapr2_rhi:
    <<: *bnf_csapr2_cmac_values
    save_name: bnfcsapr2cmacrhiS3.c1
```

`plot_values` usually differs more between PPI and RHI (PPI has lat/lon map
bounds, RHI doesn't), so it's typically spelled out separately for each.

---

## `field_names`

Maps the logical field names CMAC's processing code uses internally to the
actual field names present in your radar object / sonde dataset. All keys
below are required for a new radar entry used with `cmac()`; the last four
(`zdr_field`, `pia_field`, `phidp_field`, `refl_field`) name fields that
`cmac()` itself creates during processing, so they're typically pointed at
CMAC's own output field names rather than anything in the raw input file.

| Key | Meaning | Typical value |
|---|---|---|
| `reflectivity` | Input (raw) reflectivity field | `reflectivity` |
| `velocity` | Input radial (Doppler) velocity field | `mean_doppler_velocity` |
| `input_zdr` | Input differential reflectivity field (offset gets added to this one) | `differential_reflectivity` |
| `differential_reflectivity` | Differential reflectivity field name used downstream | `differential_reflectivity` |
| `input_phidp_field` | Input differential phase field | `differential_phase` |
| `input_clutter_corrected_reflectivity` | Reflectivity field used as input when `gen_clutter_from_refl` is enabled | `reflectivity` |
| `clutter` | Ground-clutter flag field name (read if present, or written to if `gen_clutter_from_refl` generates one) | `ground_clutter` |
| `normalized_coherent_power` | Normalized coherent power (NCP) field | `normalized_coherent_power` |
| `cross_correlation_ratio` | Copolar correlation coefficient field | `copol_correlation_coeff` |
| `signal_to_noise_ratio` | Existing SNR field name, or `null`/absent to have `cmac()` compute one from reflectivity | `signal_to_noise_ratio_copolar_h` or `null` |
| `altitude` | Sonde variable: geopotential/altitude | `alt` |
| `temperature` | Sonde variable: dry-bulb temperature | `tdry` |
| `u_wind` | Sonde variable: zonal wind component | `u_wind` |
| `v_wind` | Sonde variable: meridional wind component | `v_wind` |
| `zdr_field` | ZDR field name passed into `pyart.correct.calculate_attenuation_zphi` | `corrected_differential_reflectivity` |
| `pia_field` | Output name for path-integrated attenuation | `path_integrated_attenuation` |
| `phidp_field` | Differential phase field passed into attenuation correction | `corrected_differential_phase` |
| `refl_field` | Reflectivity field passed into attenuation correction | `corrected_reflectivity` |

Setting `signal_to_noise_ratio: null` (YAML) / `None` (JSON via
`meta_append`) tells `cmac()` to derive SNR from reflectivity with
`pyart.retrieve.calculate_snr_from_reflectivity` instead of reading an
existing field.

---

## `cmac_values`

Processing thresholds and coefficients for one radar. Every key has a
built-in fallback (listed below), applied via `cmac_config.get(key,
default)`, **except** the ones marked *(required)* — those are read with
plain dict indexing (`cmac_config[key]`) and a new radar entry omitting
them will raise `KeyError` the first time `cmac()` runs.

### Identification / site (required for a new radar)

| Key | Meaning |
|---|---|
| `save_name` | Base filename `cmac`, the CLI script, uses when writing the output CfRadial file |
| `sonde_name` | Informational: the ARM sonde datastream this radar is normally paired with |
| `site_alt` | Overrides `radar.altitude['data'][0]` (meters) before processing |

### Offsets and corrections (required)

| Key | Meaning |
|---|---|
| `ref_offset` | dB added to the raw reflectivity field before processing, and passed to `calculate_attenuation_zphi` as its `offset` |
| `zdr_offset` | dB added to `input_zdr` (or every field listed in `offset_zdrs`, if present) |
| `offset_zdrs` | *(optional list)* Field names to apply `zdr_offset` to, instead of just `input_zdr` |
| `flip_phidp` | `true`/`false` — multiply PhiDP by -1 before processing |
| `phidp_flipped` | *(optional list)* Field names to flip when `flip_phidp` is true, instead of just `input_phidp_field` |
| `gen_clutter_from_refl` | `true`/`false` — derive a clutter field from reflectivity instead of reading `clutter` from the input |
| `gen_clutter_from_refl_diff` | dBZ difference threshold used by that derivation |
| `gen_clutter_from_refl_alt` | Altitude ceiling (m) used by that derivation |
| `clutter_mask_z_for_texture` | `true`/`false` — mask velocity by `ground_clutter` before computing velocity texture |

### Attenuation / Z-PHI coefficients (required)

| Key | Meaning |
|---|---|
| `attenuation_a_coef` | `a` coefficient, specific attenuation (Z-PHI) |
| `c_coef` | `c` coefficient, specific differential attenuation |
| `d_coef` | `d` coefficient, specific differential attenuation |
| `beta_coef` | `beta` coefficient, Z-PHI |
| `self_const` | `self_const` passed to `phase_proc_lp_gf` (LP KDP method only) |

### KDP method (required)

| Key | Meaning |
|---|---|
| `kdp_method` | `"bringi"` (CSU KDP, default if unset) or `"lp"` (linear-programming, needs COIN-OR/CyLP) |

### Rain rate coefficients (required): `rate = A * moment^B`

(for the `_Z` variant, `moment` is `corrected_reflectivity` converted to
linear units, i.e. `10^(dBZ / 10)`, before the exponent is applied)

| Key |
|---|
| `rain_rate_a_coef_A`, `rain_rate_b_coef_A` — from specific attenuation |
| `rain_rate_a_coef_Z`, `rain_rate_b_coef_Z` — from corrected reflectivity |
| `rain_rate_a_coef_Kdp`, `rain_rate_b_coef_Kdp` — from specific differential phase |

### Beam blockage (required only if you pass `geotiff=` to `cmac()`)

| Key | Meaning |
|---|---|
| `beam_width` | Radar beam width in degrees |
| `radar_height_offset` | Height offset (m) for the beam-blockage calculation |
| `cbb_blockage_threshold` | *(has default 0.80)* Cumulative beam-blockage fraction above which a gate is flagged `terrain_blockage` |

### Gate-ID classifier (optional)

| Key | Default | Meaning |
|---|---|---|
| `gate_id_method` | `cmac_fuzzy` | Which classifier fills `gate_id`. `cmac_fuzzy` is CMAC's own five-class fuzzy scheme; `radar_palette` delegates to `radar_palette.gateid`. See [Gate-ID backends](#gate-id-backends). |

### Fuzzy-logic classification (optional — see below for format)

Read only when `gate_id_method` is `cmac_fuzzy`.

| Key | Meaning |
|---|---|
| `mbfs` | Custom membership functions. **Replaces the entire default dict** if set — list every class you want active. |
| `hard_const` | Custom hard constraints, replacing the default list. |
| `fuzzy_tex_start` *(default 2.0)*, `fuzzy_tex_end` *(default 2.1)* | Velocity-texture range used by the fuzzy scorer |
| `fuzzy_score_median_size` *(default `(3, 4)`)* | Median-filter kernel applied to the fuzzy score |

### radar-palette classification (optional)

Read only when `gate_id_method` is `radar_palette`. Every key left `null`
takes that classifier's own documented default, so pin one only where your
radar needs to differ.

| Key | Default | Meaning |
|---|---|---|
| `gate_id_class_map` | `null` | Class name -> CMAC category, overriding the default fold for the classes named. Partial maps are merged over the default. Targets must be one of `multi_trip`, `rain`, `snow`, `no_scatter`, `melting`. |
| `gate_id_freezing_level` | `null` | Freezing level in m MSL for the melting-layer constraints. `null` derives it from the mapped sounding, which is what a site with a sounding should use. |
| `gate_id_apply_offsets` | `true` | Add `ref_offset` / `zdr_offset` to the uncorrected moments the classifier sees. See [Gate-ID backends](#gate-id-backends). |
| `gate_id_unclassified_policy` | `warn` | What to do when the classifier declines a volume. `warn` reports and continues; `error` fails the run. See [Gate-ID backends](#gate-id-backends). |
| `gate_id_snr_min` | `3.0` | Gates below this SNR are forced to `no_scatter` before scoring. `null` disables the test. |
| `gate_id_min_run` | `3` | Class runs shorter than this many gates along a ray are dissolved. |
| `gate_id_despeckle_keep_dbz` | `30.0` | Reflectivity at or above which a gate is never despeckled or gated out. |
| `gate_id_incoherent_frac` | `null` | Velocity texture, as a fraction of the uniform-random-phase limit, above which a gate cannot be first-trip weather. Instrument-specific in practice — see below. `0` disables the test. |
| `gate_id_texture_window` | `4` | Footprint of the texture operator, in gates and rays. |
| `gate_id_publish_margin` | `false` | Also write `scatterer_classification_margin`, the winning minus runner-up score. Doubles the classification storage in the output file. |

`gate_id_incoherent_frac` is exposed per radar because it was measured not to
transfer between instruments: the fraction of precipitation gates
(Z >= 25 dBZ, RhoHV > 0.95) it rejects ranges from under 1% on weak-echo
C-band RHIs to 24.6% on an S-band NEXRAD volume. Treat it as a per-instrument
calibration, not a universal constant.

#### Which categories reach which product

The `gate_id` field is the mask behind every masked product in the file, and
each step includes a different set of categories:

| Step | Categories included |
|---|---|
| Velocity dealiasing, velocity texture | `rain`, `melting`, `snow` |
| Z-PHI attenuation correction, `corrected_reflectivity`, `specific_attenuation`, KDP filtering | `rain`, `melting`, `snow` |
| `rain_rate_A`, `rain_rate_Kdp`, `rain_rate_Z` | `rain` |
| `snow_rate_*` | `snow` |

The melting layer is a valid radar return and is included in the Z-PHI
correction, so `corrected_reflectivity` covers melting-layer gates. (Before
this branch that filter admitted `gate_id` 1 and 2 as bare literals, which
excluded melting and also assumed the fuzzy classifier's category order; the
codes now come from the field's own `notes` string.)

#### Gate-ID backends

Both backends publish the same `gate_id` field with the same five categories
in the same order — `0:multi_trip,1:rain,2:snow,3:no_scatter,4:melting`, with
`clutter` (5) and `terrain_blockage` (6) appended by `cmac()` when it has a
clutter field, a vendor classification mask or a geotiff. That ordering is a
contract: `cmac.gate_id.get_gate_id_categories` derives each code from its
position in the field's `notes` string, and the gate filter used before the
Z-PHI attenuation correction reads codes 1 and 2 as literals.

The `radar_palette` backend classifies into eleven classes and folds them
onto those five. The fold is lossy, so the eleven-class result is published
in full alongside it as `scatterer_classification` with CF
`flag_values`/`flag_meanings`:

| radar-palette class | CMAC category |
|---|---|
| `light_rain`, `moderate_rain`, `heavy_rain` | `rain` |
| `ice_snow`, `graupel_hail` | `snow` |
| `melting_wet` | `melting` |
| `multi_trip` | `multi_trip` |
| `no_scatter`, `unclassified`, `clutter`, `biological` | `no_scatter` |

`clutter` and `biological` fold to `no_scatter` rather than to CMAC's own
`clutter` category because that category is code 5 and exists only when
`cmac()` was given the inputs to add it; claiming it here would either leave
a gap in the positional `notes` contract or duplicate a label. Both classes
are excluded from meteorological gates either way, and both remain readable
in `scatterer_classification`.

`radar_palette` is not a CMAC dependency — it is imported only when a
configuration selects this backend. The classifier lives in the package's
`gateid` module, which is not yet in radar-palette's released main branch;
install it from the development branch:

```
pip install 'radar-palette @ git+https://github.com/scollis/radar-palette@gateid'
```

Selecting the backend without it installed raises an `ImportError` naming
both that install and the `cmac_fuzzy` fallback.

Two behaviours of this backend are CMAC's own and worth knowing about:

- **Classification runs on the uncorrected moments.** For each moment the
  backend takes the `uncorrected_*` field where the volume publishes one —
  `uncorrected_reflectivity_h`, `uncorrected_differential_reflectivity`,
  `uncorrected_copol_correlation_coeff`, `uncorrected_differential_phase`,
  `uncorrected_mean_doppler_velocity_h`, `uncorrected_spectral_width_h`, and
  the uncorrected NCP and SNR where they exist — and falls back to the
  radar's `field_names` entry otherwise. Deciding what the instrument saw is
  a judgement about the measurement, and the unprefixed fields on an ARM `a1`
  volume already carry vendor clutter filtering, thresholding and (on the
  CACTI and TRACER generations) attenuation correction, whose definition
  varies by site and instrument generation. Legacy platforms (MDV-era X-SAPR,
  NEXRAD) publish no uncorrected moments, so there the config remains the
  source of truth. Exactly one candidate per moment is handed to the
  classifier, so its own internal preference order cannot pick a different
  field. The field each moment resolved to is printed when `verbose=True`.
- Because `cmac()` applies `ref_offset` and `zdr_offset` in place to the
  *configured* reflectivity and ZDR, and an uncorrected moment has not been
  through that, the backend adds those offsets to its own view of them —
  calibration is a property of the instrument, not a correction. Set
  `gate_id_apply_offsets: false` to classify on the raw values instead. A
  moment that fell back to the configured field is never offset twice.
- **A volume the classifier declines is reported, not folded to clear air.**
  `radar_palette` skips sweeps it judges unsuitable — a narrow-elevation-span
  RHI, for example — and returns `unclassified` for every gate in them, which
  folds onto `no_scatter` and is then indistinguishable from empty sky: every
  masked product in the file would be empty with nothing saying why. When any
  sweep is skipped, or more than half the gates come back `unclassified`, the
  backend warns with the sweep numbers and elevation spans, and writes
  `gate_id_unclassified_gates` and `gate_id_skipped_sweeps` to the file. Set
  `gate_id_unclassified_policy: error` to make it a hard failure instead. Four
  TRACER C-SAPR2 cell-tracking RHIs (16-76 rays, elevation spans of 3.7 to
  18.8 degrees) hit this; the fuzzy classifier handles them, labelling 1,186 to
  15,434 gates rain on three of the four.
- Spectrum width has no `field_names` key (CMAC's own classifier does not use
  it, `radar_palette` does), so it is probed for by name — `spectrum_width`
  on MDV and NEXRAD volumes, `spectral_width` on modern ARM CfRadial. Add a
  `spectral_width` key to `field_names` to pin it.
- A gate with no finite *measured* moment cannot carry a hydrometeor label.
  The underlying classifier tests whether a feature is present rather than
  whether its value at a gate is finite, and gate temperature is finite
  everywhere, so empty-sky gates can otherwise score above zero on
  temperature alone. The number of gates demoted is written to the output
  file as the `gate_id_no_evidence_gates` global attribute, alongside
  `gate_id_method` and `gate_id_temperature_source`.

### Other tunables (all optional, with defaults from `_DEFAULT_PROCESSING_TUNABLES`)

| Key | Default | Meaning |
|---|---|---|
| `snow_density` | `0.073` | 1 / SWE ratio used for snowfall rate |
| `phidp_nowrap` | `50` | `nowrap` passed to `phase_proc_lp_gf` (LP method) |
| `kdp_phase_proc_max` | `10.0` | KDP ceiling for the phase-processing gate filter used before Z-PHI attenuation correction |
| `phidp_despeckle_size` | `49` | Despeckle filter size (gates) applied to differential phase before attenuation correction |
| `corrected_velocity_valid_min` | `-100.0` | `valid_min` metadata for `corrected_velocity` (only set if not already present) |
| `corrected_velocity_valid_max` | `100.0` | `valid_max` metadata for `corrected_velocity` |
| `melt_fzl_ceiling` | `5000.0` | Freezing-level ceiling (m) |
| `melt_fzl_replacement` | `3500.0` | Freezing level used when the sounding value is unrealistic |
| `melt_fzl_floor` | `1000.0` | Freezing-level floor (m) |
| `max_kdp` | `15.0` | KDP ceiling applied by `fix_phase_fields` |
| `velocity_texture_window` | `4` | Window size for velocity-texture calculation |
| `velocity_texture_median_size` | `(4, 4)` | Median-filter kernel for velocity texture |
| `area_coverage_precip_threshold` | `10.0` | dBZ threshold used by `area_coverage()` |
| `area_coverage_convection_threshold` | `40.0` | dBZ threshold used by `area_coverage()` |
| `rain_rate_valid_max` | `400` | `valid_max` clamp applied to every `rain_rate_*` field |
| `snow_rate_valid_max` | `500` | `valid_max` clamp applied to every `snow_rate_*` field |

#### `mbfs` format

`mbfs` is a mapping of classification name -> field name -> `[[x1, x2, x3,
x4], weight]`, where `[x1, x2, x3, x4]` is a trapezoidal membership
function over that field's values and `weight` scales that field's
contribution to the class's fuzzy score. The classification names CMAC
expects are `rain`, `snow`, `melting`, `multi_trip`, and `no_scatter`:

```yaml
cmac_values:
  my_radar_ppi:
    mbfs:
      rain:
        velocity_texture:          [[0, 0, 2.0, 2.1], 0.0]
        copol_correlation_coeff:   [[0.97, 0.98, 1, 1], 2.0]
        normalized_coherent_power: [[0.4, 0.5, 1, 1], 0.0]
        height:                    [[0, 0, 5000, 6000], 0.0]
        sounding_temperature:      [[2.0, 5.0, 100, 100], 2.0]
        signal_to_noise_ratio:     [[-2, 2, 1000, 1000], 1.0]
      snow: {...}
      melting: {...}
      multi_trip: {...}
      no_scatter: {...}
```

Setting `mbfs` overrides the built-in dict wholesale — a partial override
(e.g. redefining only `rain`) will leave the other classes undefined and
break classification, so always list all five classes together.

#### `hard_const` format

A list of `[class, field, [lower, upper]]` triples. Any gate already
classified as `class` gets forced back to `no_scatter` if `field`'s value
at that gate falls outside `[lower, upper]`:

```yaml
cmac_values:
  my_radar_ppi:
    hard_const:
      - [melting, sounding_temperature, [-10000, -2]]
      - [rain, sounding_temperature, [-1000, -5]]
      - [snow, sounding_temperature, [3, 100]]
```

---

## `plot_values`

Consumed by `quicklooks_ppi`/`quicklooks_rhi`. Every key has a default
from `_DEFAULT_PLOT_FIELD_RANGES` / `_DEFAULT_PLOT_LAYOUT`, so a new radar
entry only strictly needs `sweep` and, for PPI, the map bounds.

| Key | Default | Meaning |
|---|---|---|
| `sweep` | — | Sweep index used for single-sweep quicklooks |
| `min_lat`, `max_lat`, `min_lon`, `max_lon` | — | Map bounds (PPI only — omit for RHI configs) |
| `reflectivity_raw_vmin` / `_vmax` | `-8` / `64` | Color range, raw reflectivity |
| `reflectivity_vmin` / `_vmax` | `-8` / `40` | Color range, `reflectivity` panel |
| `corrected_reflectivity_vmin` / `_vmax` | `0` / `40` | Color range, attenuation-corrected reflectivity |
| `corrected_velocity_vmin` / `_vmax` | `-60` / `60` | Color range, dealiased velocity |
| `velocity_texture_vmin` / `_vmax` | `0` / `14` | Color range, velocity texture |
| `cross_correlation_ratio_vmin` / `_vmax` | `0.5` / `1.0` | Color range, correlation coefficient |
| `specific_attenuation_vmin` / `_vmax` | `0` / `1.0` | Color range, specific attenuation |
| `corrected_specific_diff_phase_vmin` / `_vmax` | `0` / `6` | Color range, KDP |
| `filtered_corrected_differential_phase_vmin` / `_vmax` | `0` / `360` | Color range, filtered PhiDP |
| `filtered_corrected_specific_diff_phase_vmin` / `_vmax` | `-2` / `10` | Color range, filtered KDP |
| `rain_rate_vmin` / `_vmax` | `0` / `120` | Color range, rain rate panels |
| `snow_rate_vmin` / `_vmax` | `0` / `50` | Color range, snow rate panels |
| `figsize_single` | `[12, 8]` | Figure size, single-panel plots |
| `figsize_panel` | `[15, 10]` | Figure size, the four-panel plot |
| `lat_lon_tick_spacing` *(PPI only)* | `0.8` | Degrees between map gridlines |
| `dd_lobe_grid_spacing` *(PPI only)* | `0.01` | Grid spacing (degrees) for the dual-Doppler lobe overlay (`dd_lobes=True`) |
| `dd_lobe_bca_levels` *(PPI only)* | `[pi/6, 5*pi/6]` | Beam-crossing-angle contour levels for the DD lobe overlay |
| `sweep_fallback_nsweeps_lt` *(RHI only)* | `4` | If the radar has fewer sweeps than this... |
| `sweep_fallback` *(RHI only)* | `2` | ...use this sweep index instead of `sweep` |
| `ymin`, `ymax` *(RHI only)* | `0`, `10` | Height axis limits (km) for RHI cross-section panels |
| `cat_colors` | see below | `gate_id` category -> color, for the classification panel |

`cat_colors` default:

```yaml
cat_colors:
  rain: green
  multi_trip: red
  no_scatter: gray
  snow: cyan
  melting: yellow
  clutter: black
  terrain_blockage: brown
```

---

## `metadata` and `default_metadata`

`metadata.<config_name>` supplies the global (file-level) NetCDF attributes
written to the output radar object when `cmac(..., meta_append="config")`
is used (this is also what the `cmac` CLI script defaults to). Keys are
free-form — they become attributes as-is — but the built-in radars
consistently use:

```yaml
metadata:
  my_radar_ppi:
    site_id: bnf
    facility_id: s3
    comment: "..."
    attributions: "..."
    version: "2.0 lite"
    vap_name: cmac
    known_issues: "..."
    developers: "Your Name, Your Institution."
    translator: "..."
    mentors: "..."
    Conventions: "CF/Radial instrument_parameters ARM-1.3"
    references: "..."
    source: "..."
    institution: "..."
    doi: "..."
```

`default_metadata` (top-level, not per-radar) is the fallback metadata used
when `meta_append` is `None` or `"default"` instead of `"config"` — it's a
single dict shared across all radars, meant for generic/no-config runs
rather than a specific instrument.

`meta_append` also accepts a path to a `.json` file as a third option, read
verbatim instead of anything in this YAML file.

---

## `zs_relationships`

Not per-radar — a flat mapping of relationship name -> `{A, B,
abbreviation}`, used for `S = (1 / snow_density) * (Z_linear / A)^(1 / B)`
snowfall-rate fields, where `Z_linear = 10^(corrected_reflectivity / 10)`
and `snow_density` comes from `cmac_values.<config_name>.snow_density`
(default `0.073`). Entries here add to (or override, by name) the built-in
set:

```yaml
zs_relationships:
  My Lab Relationship:
    A: 95
    B: 1.85
    abbreviation: mylab
```

`abbreviation` becomes the field-name suffix: the field is added as
`snow_rate_<abbreviation>`. Built-in relationships: `Wolf and Snider
(2012)` (`ws2012`), `WSR 88D High Plains` (`ws88diw`), `Matrosov et
al.(2009) Braham(1990) 1` (`m2009_1`), `Matrosov et al.(2009) Braham(1990)
2` (`m2009_2`).

---

## Full example

See `configs/bnfcsapr2.yaml` for a complete file covering `metadata`,
`field_names`, `cmac_values` (including custom `mbfs`/`hard_const`), and
`plot_values` for both a PPI and an RHI scan strategy of the same radar,
and `documents/example_config.yaml` for a shorter file that overrides one
existing radar and defines a minimal new one.
