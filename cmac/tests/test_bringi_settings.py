"""Tests for YAML-configurable Bringi KDP settings."""

import numpy as np
import pytest

from cmac.cmac_radar import _get_bringi_options


def test_bringi_options_default_and_override():
    assert _get_bringi_options({}) == {"nfilter": 1, "window": 3.0}
    assert _get_bringi_options(
        {
            "bringi_nfilter": 2,
            "bringi_window": 6,
        }
    ) == {"nfilter": 2, "window": 6.0}


@pytest.mark.parametrize(
    "config",
    [
        {"bringi_nfilter": 0},
        {"bringi_nfilter": -1},
        {"bringi_nfilter": 1.5},
        {"bringi_nfilter": True},
        {"bringi_window": 0},
        {"bringi_window": -3},
        {"bringi_window": np.inf},
        {"bringi_window": False},
    ],
)
def test_bringi_options_reject_invalid_values(config):
    with pytest.raises(ValueError):
        _get_bringi_options(config)
