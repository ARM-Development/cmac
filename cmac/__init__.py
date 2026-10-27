"""
====
CMAC
====

CMAC functions for determining gate ids, detect second trip returns and
more.

    cmac
    quicklooks
    snr_and_sounding
    get_texture
    cum_score_fuzzy_logic
    do_my_fuzz
    return_csu_kdp
    retrieve_qvp
    tall_clutter

"""

from .cmac_radar import cmac, area_coverage
from .cmac_ppi_quicklooks import quicklooks_ppi
from .cmac_rhi_quicklooks import quicklooks_rhi
from .cmac_processing import snr_and_sounding, do_my_fuzz
from .cmac_processing import get_texture, cum_score_fuzzy_logic
from .cmac_processing import return_csu_kdp, retrieve_qvp, beam_block
from .config import get_cmac_values, get_field_names
from .config import get_metadata, get_plot_values
from .config import get_zs_relationships, get_default_metadata
from .gate_id import (append_gate_id_category, get_gate_id_categories,
                      gate_id_has_category)
from .gate_id_backends import (radar_palette_available, radar_palette_gate_id,
                               sounding_freezing_level)
from .data_catalouging import get_sounding_times, get_sounding_file_name
from .radar_clutter import tall_clutter

__all__ = [s for s in dir() if not s.startswith('_')]
