# Changelog

## New Features

### Typed vectors with swizzle support (Vec2, Vec3, Vec4, Vec5)

The `Vector` class is now backed by numpy for fast array operations. In addition to the
general-purpose `Vector`, four fixed-dimension types with GLSL-style swizzle
properties are available:

```python
from piscript.VectorUtils import Vec3, Vec2

v = Vec3(1, 2, 3)
v.xy          # Vec2(1.0, 2.0)
v.zyx         # Vec3(3.0, 2.0, 1.0)
v.z = 99      # single-component assignment
v.xy = (5, 6) # multi-component assignment
```

All arithmetic operations (`+`, `-`, `*`, `/`, `-v`) preserve the vector type.

### Cross-platform TeX font detection

Font resolution now uses the system `kpsewhich` command (bundled with every TeX
distribution) instead of requiring matplotlib. On Windows, macOS, and Linux, if
TeX Live or MiKTeX is installed and on `PATH`, fonts are found automatically.
matplotlib is still used as a fallback if available.

The library can now be installed with `pip install .` (see `pyproject.toml`).

## Bug Fixes

### `settexmacros()` now calls the correct method

Previously `settexmacros(s)` silently called `settexprefix(s)` instead — a
copy-paste bug. It now correctly calls `settexmacros`.

### `Face.__init__` stores extra arguments correctly

`Face(polygon, color, extra1, extra2)` now properly stores extra arguments in
`self.extras`. Previously they were written to a local variable and discarded.

### `Type1Font` no longer crashes on missing font files

When a `.pfb` font file cannot be opened, the error is now a clear
`FileNotFoundError`. Previously a secondary `AttributeError` in the destructor
masked the real problem.

### Font resolution no longer recurses infinitely

When a font is not found and the fallback ("Courier") also cannot be found, the
library now returns `None` gracefully instead of entering infinite recursion
(`RecursionError`).

### `envelope()` and `setbbox()` now work

`bbox.py` and any script using `envelope()` / `setbbox()` to adjust bounding
boxes now functions correctly. These methods were referenced by the API but
never implemented.

### `Arrows` error handling uses exceptions

`arcarrow()` and `arcnarrow()` now raise `ValueError` with a descriptive message
when called with too few arguments, instead of printing to stdout and calling
`sys.exit(1)` (which killed the entire Python process).

### Broken example files fixed

`examples/vector.py` (imported a nonexistent `Vectors` module) and
`examples/path.py` (imported a nonexistent `configs.TexConfig`) have been
rewritten as working examples.

## API Changes (backward-compatible)

### Duplicate function names deprecated

The following aliases still work but now emit a `DeprecationWarning`.
Code should migrate to the canonical names:

| Deprecated        | Use instead            |
|-------------------|------------------------|
| `seteye()`        | `set_eye()`            |
| `geteye()`        | `get_eye()`            |
| `setlight()`      | `set_light()`          |
| `getlight()`      | `get_light()`          |
| `projection2d()`  | `project_to_2d()`      |
| `smoothconvexsurface()` | `smooth_convex_surface()` |
| `affine_reflect()`| `reflect()`            |

### Better error when `init()` hasn't been called

Calling any PiModule wrapper function (e.g. `moveto()`, `stroke()`) before
`init()` now raises a clear `RuntimeError`:

> PiScript not initialized. Call init() or init3d() first.

Previously this produced an opaque `AttributeError: 'NoneType' object has no attribute 'moveto'`.

### `convex_surface(f)` fixed

`convex_surface(f)` previously contained dead code that always returned
`Vector(1, 0, 0)`. It now correctly creates a `ConvexSurface` from the given face.

### `__version__` available

```python
import piscript
print(piscript.__version__)  # "0.1.0"
```
