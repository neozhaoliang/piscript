"""PostScript-safe character table.

Maps byte values 0-255 to PostScript string-safe representations.
Control characters (0-31, 127) and high bytes (128-255)
use octal notation; printable ASCII (32-126) use the literal character.
"""

toReadable = [
    f"\\{i:03o}" for i in range(256)
]
# Make printable ASCII (32-126) use the literal character
for i in range(32, 127):
    toReadable[i] = chr(i)
