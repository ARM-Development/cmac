"""Unit tests for the gate_id category-metadata helpers."""

import pytest

from cmac.gate_id import (append_gate_id_category, gate_id_has_category,
                          get_gate_id_categories)

FUZZY_NOTES = '0:multi_trip,1:rain,2:snow,3:no_scatter,4:melting'


def test_categories_are_positional():
    categories = get_gate_id_categories({'notes': FUZZY_NOTES})
    assert categories == {'multi_trip': 0, 'rain': 1, 'snow': 2,
                          'no_scatter': 3, 'melting': 4}


def test_append_returns_the_next_code():
    field = {'notes': FUZZY_NOTES}
    assert append_gate_id_category(field, 'clutter') == 5
    assert field['notes'] == FUZZY_NOTES + ',5:clutter'
    assert field['valid_min'] == 0
    assert field['valid_max'] == 5
    assert gate_id_has_category(field, 'clutter')


def test_append_is_idempotent():
    """Two sources of clutter must not append the label twice.

    A volume with both a ground_clutter field and a vendor
    classification_mask hits this path once for each. Because codes are
    positional, a duplicate label used to shift clutter to 6 while the gates
    themselves had been set to 5.
    """
    field = {'notes': FUZZY_NOTES}
    first = append_gate_id_category(field, 'clutter')
    second = append_gate_id_category(field, 'clutter')
    assert first == second == 5
    assert field['notes'].count('clutter') == 1
    assert get_gate_id_categories(field)['clutter'] == 5


def test_append_keeps_later_categories_consistent():
    field = {'notes': FUZZY_NOTES}
    append_gate_id_category(field, 'clutter')
    append_gate_id_category(field, 'clutter')
    blockage = append_gate_id_category(field, 'terrain_blockage')
    assert blockage == 6
    categories = get_gate_id_categories(field)
    assert categories['clutter'] == 5
    assert categories['terrain_blockage'] == 6
    assert field['valid_max'] == 6


def test_append_needs_notes():
    with pytest.raises(KeyError):
        append_gate_id_category({'flag_meanings': 'rain snow'}, 'clutter')
