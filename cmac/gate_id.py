"""
Helpers for interpreting the category metadata attached to a ``gate_id``
(hydrometeor ID) radar field.

CMAC's own gate id fields document their categories with a ``notes``
attribute, which in practice shows up in a few different shapes:

- ``"0: multi_trip, 1: rain, 2: snow"`` -- comma separated ``"index: label"``
  pairs, colon separated.
- ``"0 multi_trip, 1 rain, 2 snow"`` -- comma separated ``"index label"``
  pairs, whitespace separated.
- ``"multi_trip rain snow melting no_scatter clutter terrain_blockage"`` --
  a plain, unindexed list of labels in order, with no indices or commas at
  all.

Fields that follow the CF conventions instead (or radar objects re-read
from a file that converted ``notes`` on save) may document the same
information with a ``flag_meanings`` attribute and a parallel
``flag_values`` attribute (the matching integer codes). ``flag_meanings``
is generally comma separated, though a plain whitespace separated string
is also accepted.
"""

import re

_PAIR_SEP_RE = re.compile(r'[:\s]+')


def _label_from_pair(pair_str):
    """Extract the category label from a single ``"index: label"`` pair,
    where the index/label separator is a colon, whitespace, or both."""
    parts = _PAIR_SEP_RE.split(pair_str.strip(), maxsplit=1)
    return parts[-1].strip()


def _split_list(text):
    """Split a comma or whitespace separated list of labels into its
    individual, stripped entries."""
    if ',' in text:
        parts = text.split(',')
    else:
        parts = text.split()
    return [part.strip() for part in parts if part.strip()]


def _labels_from_notes(notes):
    """Return the ordered list of category labels encoded in a ``notes``
    attribute, handling both indexed ``"index: label"``/``"index label"``
    pairs and a plain, unindexed list of labels."""
    pieces = [p.strip() for p in notes.split(',') if p.strip()]
    if len(pieces) > 1 or (pieces and ':' in pieces[0]):
        return [_label_from_pair(piece) for piece in pieces]
    return _split_list(notes)


def get_gate_id_categories(gate_id_field):
    """
    Return a dict mapping each gate id category label to its integer code.

    Parameters
    ----------
    gate_id_field : dict
        A Py-ART field dictionary, e.g. ``radar.fields['gate_id']``.

    """
    if 'notes' in gate_id_field:
        labels = _labels_from_notes(gate_id_field['notes'])
        return {label: i for i, label in enumerate(labels)}

    if 'flag_meanings' in gate_id_field and 'flag_values' in gate_id_field:
        labels = _split_list(gate_id_field['flag_meanings'])
        values = gate_id_field['flag_values']
        return {label: int(value) for label, value in zip(labels, values)}

    raise KeyError(
        "The 'gate_id' field must have either a 'notes' attribute or "
        "'flag_values'/'flag_meanings' attributes describing its "
        "categories.")


def append_gate_id_category(gate_id_field, category):
    """
    Ensure ``category`` is documented on a ``gate_id`` field, and return the
    integer code it occupies.

    The ``notes`` attribute is positional: :func:`get_gate_id_categories`
    reads a category's code from where its label sits in the string, not from
    the integer printed next to it. Appending the same label twice therefore
    shifts every subsequent code by one -- a volume carrying both a
    ``ground_clutter`` field and a vendor ``classification_mask`` had
    ``,5:clutter`` appended once for each, after which ``clutter`` resolved to
    6 while the gates themselves had been set to 5.

    Appending through this function instead is idempotent: a category already
    present returns its existing code and the notes string is left alone. The
    code is returned rather than assumed so callers do not have to hard-code
    it, which is what made the duplication possible in the first place.

    Parameters
    ----------
    gate_id_field : dict
        A Py-ART field dictionary with a ``notes`` attribute, e.g.
        ``radar.fields['gate_id']``. Modified in place.
    category : str
        Category label, e.g. ``'clutter'``.

    Returns
    -------
    code : int
        The integer code for ``category``.

    """
    if 'notes' not in gate_id_field:
        raise KeyError(
            "Cannot append a category to a 'gate_id' field with no 'notes' "
            "attribute describing the categories it already has.")

    labels = _labels_from_notes(gate_id_field['notes'])
    if category in labels:
        return labels.index(category)

    code = len(labels)
    gate_id_field['notes'] = '%s,%d:%s' % (
        gate_id_field['notes'], code, category)
    gate_id_field['valid_min'] = 0
    gate_id_field['valid_max'] = code
    return code


def gate_id_has_category(gate_id_field, category):
    """
    Return True if ``category`` is one of the documented categories of a
    ``gate_id`` field, whether documented via ``notes`` or via
    ``flag_meanings``.
    """
    if 'notes' in gate_id_field:
        return category in _labels_from_notes(gate_id_field['notes'])
    if 'flag_meanings' in gate_id_field:
        return category in _split_list(gate_id_field['flag_meanings'])
    return False
