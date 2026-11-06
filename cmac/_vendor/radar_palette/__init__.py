"""Vendored radar-palette components used by CMAC's gate-ID backend.

Only the gate-ID implementation is included here; the rest of radar-palette
is intentionally not part of CMAC's vendored surface.
"""

from . import gateid

__all__ = ["gateid"]
