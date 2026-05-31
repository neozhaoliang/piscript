# PiScript

A Python library for generating PostScript graphics with TeX-quality text rendering.

This is the Python 3 port of PiScript (originally written for Python 2). Below are all user-visible changes when migrating from the Python 2 version.

## Installation

| Item | Python 2 | Python 3 |
|------|----------|----------|
| Python version | 2.7 | 3.10+ |
| Numpy | Not required | Required |
| `BuildChar` module | Available | Removed (was unused) |
| `DviPS` module | Available | Not ported |
| `Path` module | Available | Not ported |
| `Colors` module | Available | Not ported |
| `Curve` module | Available | Not ported |
| `Eigs2d` module | Available | Not ported |
| `MatrixUtils` module | Available | Not ported |

## PiModule — Top-Level API

### Removed functions

These functions existed in Python 2 `PiModule` but have been removed in Python 3. Most were no-ops (pass stubs on Canvas) that never produced output.

| Function | Notes |
|----------|-------|
| `draw(path)` | Not implemented |
| `boundary(*args)` | Not implemented |
| `location(*args)` | Not implemented |
| `eol()` | Not implemented |
| `importPFB(f)` | Not implemented |
| `graph(*args)` | Not implemented |
| `grid(N, ds)` | Not implemented |
| `rcurveto(*args)` | Not implemented |
| `charpath(s, *args)` | Not implemented |
| `charpath3d(s, *args)` | Not implemented |
| `box(*args)` | Removed — was a no-op stub |
| `parallelogram(*args)` | Removed — was a no-op stub |
| `texpath(*args)` | Removed — was a no-op stub |
| `quadarrow(*args)` | Removed — was a no-op stub |
| `arrowheadlength()` | Removed — was a no-op stub (returned None) |
| `font(fn)` | Removed — was a Type1Font wrapper |
| `append(path)` | Not implemented |

### Deprecated wrappers

These functions are still available but will show a `DeprecationWarning`:

| Old name | Use instead |
|----------|-------------|
| `affine_reflect(f)` | `reflect(f)` |
| `seteye(e)` | `set_eye(e)` |
| `geteye()` | `get_eye()` |
| `setlight(L)` | `set_light(L)` |
| `getlight()` | `get_light()` |
| `projection2d(*args)` | `project_to_2d(*args)` |
| `smoothconvexsurface(f)` | `smooth_convex_surface(f)` |

### `init()` calling conventions (new)

Python 2 only supported `init(filename, w, h)`. Python 3 also supports:

```python
init(w, h)                  # auto-named from script filename
init(w, h, "filename.eps")  # numbers first, filename last
init("filename.eps", w, h)  # filename first (Python 2 style)
```

## Canvas — Drawing API

### Removed methods

These Canvas methods existed in Python 2 but are removed in Python 3. They were either no-ops or replaced by external module functions (passed `ps` as first argument).

| Method | Replacement |
|--------|-------------|
| `Canvas.arc(*args)` | Use `arc(*args)` from PiModule (calls `Arc.arc(ps, *args)`) |
| `Canvas.arcn(*args)` | Use `arcn(*args)` |
| `Canvas.circle(*args)` | Use `circle(*args)` |
| `Canvas.arrow(*args)` | Use `arrow(*args)` |
| `Canvas.openarrow(*args)` | Use `openarrow(*args)` |
| `Canvas.setarrowdims(*args)` | Use `setarrowdims(*args)` |
| `Canvas.texarrow(*args)` | Use `texarrow(*args)` |
| `Canvas.arcarrow(*args)` | Use `arcarrow(*args)` |
| `Canvas.arcnarrow(*args)` | Use `arcnarrow(*args)` |
| `Canvas.quadarrow(*args)` | Use `quadarrow(*args)` |
| `Canvas.ArcArrow(c, r, a, b)` | Use `ArcArrow(c, r, a, b)` |
| `Canvas.ArcnArrow(c, r, a, b)` | Use `ArcnArrow(c, r, a, b)` |
| `Canvas.arrowhead(A)` | Use `arrowhead(A)` |
| `Canvas.arrowheadlength()` | Removed |
| `Canvas.parallelogram(*args)` | Removed |
| `Canvas.polygon(*args)` | Removed |
| `Canvas.boundedbox(...)` | Kept |
| `Canvas.dimensions(s)` | Removed |
| `Canvas.charpath(s, ...)` | Removed |
| `Canvas.arcto(*args)` | Removed (returned None) |
| `Canvas.rquadto(*args)` | Removed |
| `Canvas.rcurveto(*args)` | Removed |

### Changed methods

| Method | Python 2 | Python 3 |
|--------|----------|----------|
| `fill(*args)` | Manual color parsing | Uses `VectorUtils.parse_color` |
| `stroke(*args)` | Manual color parsing | Uses `VectorUtils.parse_color` |
| `setcolor(*args)` | Manual color parsing | Uses `VectorUtils.parse_color` |

## Arrows — Arrow API

### Changed behavior

| Item | Python 2 | Python 3 |
|------|----------|----------|
| `setarrowdims(ps, *args)` | Used `global` statements to mutate module-level variables | Uses a container object (`_d.sw`, `_d.hw`, etc.) |

## Bug Fixes

| Issue | Python 2 behavior | Python 3 behavior |
|-------|-------------------|-------------------|
| `W0`/`X0`/`Y0`/`Z0` command indices | Passed class objects as indices (silently wrong) | Use correct integer constants (147, 152, 161, 166) |
| `Arrow.rotate` in `QuadShaft` | Called instance method on list (would crash) | Calls `Arrow.Rotate` static method correctly |
| `XXX.execute` via reflection | `execXXX` referenced nonexistent `getString()` | Uses `dvc.x` attribute directly |

## Import Path Changes

| Import | Python 2 | Python 3 |
|--------|----------|----------|
| `Font` class | `from piscript.Font import Font` | `from piscript.DeviceFont import Font` |
| `Font.py` | Separate module | Merged into `DeviceFont.py` |
| `VectorUtils` alias | `from piscript.PiScript3d import *` re-exports `VU` | Same, via `import piscript.VectorUtils as VU` in PiScript3d |

## Internal Changes (not user-visible)

The Python 3 codebase has been significantly refactored to reduce boilerplate while preserving the same public API:

- `Canvas.py`: `_emit()`/`_unpack_point()` helpers replace repeated patterns
- `DviReader.py`: Factory-generated command classes replace hand-written duplicates; auto-dispatch `execute()` via base class
- `PiModule.py`: Auto-proxy wrappers replace 100+ manual pass-through functions (799→320 lines)
- `PiScript3d.py`: `_move3d()` helper unifies absolute/relative 3D drawing method pairs
- `Arrows.py`: `_Transformable` mixin shares `translate()`/`rotate()` across 5 component classes
- `DviToDevice.py`: `execSetRule`/`execPutRule` aliased; dead `_renderWithChars` path removed
- `DeviceFont.py`: Merged `Font.py` (27 lines → class inside DeviceFont)
- `BuildChar.py`: Deleted (unused, import was commented out)
- Net reduction: ~1500 lines with no public API loss
