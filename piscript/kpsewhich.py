"""TeX resource file finder.

Uses matplotlib's dviread.find_tex_file (fast, in-process) as primary.
Falls back to kpsewhich CLI only when matplotlib is not available.
"""

import os
import subprocess
import shutil

VF_TYPE = "vf"
TFM_TYPE = "tfm"
ENC_TYPE = "enc"
TYPE1_TYPE = "type1 fonts"
FONTMAP_TYPE = "map"


def _find_matplotlib(name):
    """Use matplotlib's built-in kpathsea bindings (fast, in-process)."""
    try:
        from matplotlib.dviread import find_tex_file
        return find_tex_file(name)
    except (ImportError, FileNotFoundError):
        return None


_kpsewhich_path = None


def _get_kpsewhich():
    global _kpsewhich_path
    if _kpsewhich_path is None:
        _kpsewhich_path = shutil.which("kpsewhich") or ""
    return _kpsewhich_path or None


def _run_kpsewhich(name, kind=None):
    """Run kpsewhich CLI (slow — spawns a process). Fallback only."""
    kpse = _get_kpsewhich()
    if not kpse:
        return None
    args = [kpse]
    if kind:
        args.extend(["-format", kind])
    args.append(name)
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip()
            if os.path.isfile(path):
                return path
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


_KIND_EXTENSIONS = {
    "tfm": [".tfm"],
    "type1 fonts": [".pfb", ".pfa"],
    "enc": [".enc"],
    "vf": [".vf"],
    "map": [".map"],
}

_not_found = set()


def find(name, kind=None):
    """Find a TeX resource file in the texmf tree."""
    cache_key = (name, kind)
    if cache_key in _not_found:
        return None
    # Try with relevant extensions first (matplotlib needs explicit extensions)
    if not os.path.splitext(name)[1]:
        for ext in _KIND_EXTENSIONS.get(kind or "", []):
            path = _find_matplotlib(name + ext)
            if path:
                return path
    path = _find_matplotlib(name)
    if path:
        return path
    path = _run_kpsewhich(name, kind)
    if path:
        return path
    _not_found.add(cache_key)
    return None
