# PiScript

A Python 3 library for generating PostScript graphics with TeX-quality text rendering.

## Recent Changes (2026-05)

### `init()` now accepts `init(w, h, filename)` calling convention

Previously `init()` only supported `init(filename, w, h)` (filename first). It now also accepts numbers first:

```python
init(400, 300, "output.eps")   # now works
init("output.eps", 400, 300)   # still works
init(400, 300)                 # still works (auto-named from script)
```

### Removed dead stub methods from `Canvas`

Methods that were no-ops (`pass`) and never implemented have been removed:
`arc`, `arcn`, `circle`, `parallelogram`, `polygon`, `box`, `grid`, `arrow`, `openarrow`, `setarrowdims`, `quadarrow`, `texarrow`, `arcarrow`, `arcnarrow`, `dimensions`, `charpath`, `arcto`, `ArcArrow`, `ArcnArrow`, `arrowhead`, `arrowheadlength`, `rquadto`, `rcurveto`

These functions are available via `Arc.py` and `Arrows.py` (called from PiModule's top-level API), but calling them as Canvas methods now raises `AttributeError` instead of silently doing nothing.

### `setgray()` preserved as alias for `setcolor()`

```python
setgray(0.5)   # equivalent to setcolor(0.5)
```

### `VU` (VectorUtils) available in 3D mode

`piscript.VectorUtils` is imported as `VU` in `PiScript3d` and re-exported via `from PiModule import *` when using `init3d()`.

### Arrow dimensions use `_d` container

`Arrows.py` no longer uses `global` statements for dimension variables (`sw`, `hw`, `A`, `B`). They are now attributes of a `_d` container object. This does not affect the public API (`setarrowdims()` works as before).

### `BuildChar.py` removed

The charstring-to-PostScript conversion module was unused (import commented out since Python 2 port).

### `Font.py` merged into `DeviceFont.py`

The `Font` class now lives in `DeviceFont.py`. The import path `from piscript.DeviceFont import Font` replaces the old `from piscript.Font import Font`.

### Internal refactoring (non-user-facing)

- `Canvas.py`: `_emit()` and `_unpack_point()` helpers reduce boilerplate
- `DviReader.py`: Factory-generated command classes replace hand-written duplicates
- `PiModule.py`: `_make_proxy()` wrappers and `__all__` support star imports (799→320 lines)
- `PiScript3d.py`: `_move3d()` unifies 8 absolute/relative 3D drawing methods
- `Arrows.py`: `_Transformable` mixin shares `translate()`/`rotate()` across 5 classes
- `DviToDevice.py`: Removed dead `_renderWithChars` path; `execSetRule`/`execPutRule` aliased
- Net reduction: ~1500 lines with zero functionality loss
