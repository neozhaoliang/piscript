"""Command codes for the Canvas → PostScript pipeline.

Each graphics operation gets a unique integer code used as an index
into the Canvas command array and the PSExec dispatch table.
"""

import piscript.Fstr as Fstr

# Single source of truth: (name, skip_count) for each command.
# The index position doubles as the command code.
_COMMANDS = [
    ("setlinewidth", 2),
    ("setlinecap", 2),
    ("setlinejoin", 2),
    ("setdash", 3),
    ("setmiterlimit", 2),
    ("setcolor", 4),
    ("scalelinewidth", 2),
    ("newpath", 1),
    ("moveto", 3),
    ("lineto", 3),
    ("curveto", 7),
    ("fill", 1),
    ("stroke", 1),
    ("cfill", 4),
    ("cstroke", 4),
    ("clip", 1),
    ("setfont", 3),
    ("show", 3),
    ("embed", 2),
    ("closepath", 1),
    ("insert", 2),
    ("importps", 3),
    ("importeps", 3),
    ("gsave", 1),
    ("grestore", 1),
    ("shfill", 3),
    ("comment", 2),
    ("image", 5),
]

# Auto-generate constants and lookup tables
for _i, (_name, _skip) in enumerate(_COMMANDS):
    globals()[_name.upper()] = _i

Skip = [_skip for _, _skip in _COMMANDS]
Name = [_name for _name, _ in _COMMANDS]
CmdNo = len(_COMMANDS)


def to_string(cmd):
    """Debug helper: format a command array as a readable string."""
    import piscript.Canvas as Canvas  # late import to break circular dep

    parts = []
    i = 0
    n = len(cmd)
    while i < n:
        c = cmd[i]
        skip = Skip[c]
        parts.append(f"<{Name[c]}>")
        for j in range(1, skip):
            v = cmd[i + j]
            if isinstance(v, float):
                parts.append(f" {Fstr.cstr(v)},")
            elif isinstance(v, Canvas.Canvas):
                parts.append(f"\n\n{{{v}}}\n,")
            else:
                parts.append(f" {v},")
        i += skip
        parts.append("\n")
    return "".join(parts)
