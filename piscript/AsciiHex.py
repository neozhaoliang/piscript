"""ASCIIHexEncode / ASCIIHexDecode filters for PostScript PFB font data."""

import binascii


def asciihex_encode(data, errors="strict", lineLength=40):
    """Encode binary data as ASCIIHex. Returns (encoded_str, original_len)."""
    if isinstance(data, str):
        data = data.encode("latin-1")
    hex_str = binascii.hexlify(data).decode("ascii").upper()
    if lineLength and len(hex_str) > lineLength * 2:
        hex_str = "\n".join(
            hex_str[i:i + lineLength * 2]
            for i in range(0, len(hex_str), lineLength * 2)
        )
    return (hex_str, len(data))


def asciihex_decode(data, errors="strict"):
    """Decode ASCIIHex data to bytes. Returns (decoded_bytes, bytes_consumed)."""
    if isinstance(data, str):
        data = data.encode("ascii")
    # Filter out whitespace and stop at '>'
    filtered = bytearray()
    for c in data:
        if c in (0x20, 0x09, 0x0D, 0x0A, 0x0C, 0x0B):  # whitespace
            continue
        if c == 0x3E:  # '>'
            break
        filtered.append(c)
    return (binascii.unhexlify(bytes(filtered)), len(data))
