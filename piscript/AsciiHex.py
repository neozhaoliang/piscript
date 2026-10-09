"""ASCIIHexEncode / ASCIIHexDecode filters for PostScript PFB font data."""

import binascii


def asciihex_encode(data, errors="strict", lineLength=40):
    """Encode binary data as ASCIIHex. Returns (encoded_str, original_len)."""
    if isinstance(data, str):
        data = data.encode("latin-1")
    hex_str = binascii.hexlify(data).decode("ascii").upper()
    if lineLength and len(hex_str) > lineLength * 2:
        hex_str = "\n".join(
            hex_str[i : i + lineLength * 2] for i in range(0, len(hex_str), lineLength * 2)
        )
    return (hex_str, len(data))


def asciihex_decode(data, errors="strict"):
    """Decode ASCIIHex data to bytes. Returns (decoded_bytes, bytes_consumed)."""
    if isinstance(data, str):
        data = data.encode("ascii")
    # PostScript ASCIIHex allows whitespace and an optional odd final nibble.
    filtered = bytearray()
    consumed = len(data)
    for index, byte in enumerate(data):
        if byte == ord(">"):
            consumed = index + 1
            break
        if byte not in b" \t\r\n\f\v":
            filtered.append(byte)
    if len(filtered) % 2:
        filtered.append(ord("0"))
    try:
        decoded = binascii.unhexlify(filtered)
    except binascii.Error as error:
        raise ValueError("invalid PostScript ASCIIHex data") from error
    return decoded, consumed
