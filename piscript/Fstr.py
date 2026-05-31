"""Number formatting utilities for PostScript output."""

import numbers


def fstr(x):
    """Format a number in compact scientific notation (e.g. 1.5e+02)."""
    if isinstance(x, numbers.Integral):
        return str(x)
    mantissa, exp = f"{x:.6e}".split("e")
    mantissa = mantissa.rstrip("0")
    if mantissa.endswith("."):
        mantissa += "0"
    return f"{mantissa}e{exp}"


def cstr(x):
    """Format a number as a compact decimal string."""
    if isinstance(x, int):
        return str(x)
    return f"{x:.4g}"
