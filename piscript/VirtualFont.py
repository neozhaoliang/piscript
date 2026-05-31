import piscript.DviFont as DviFont
from piscript.knuth import knuth

import logging

logging.basicConfig(level=logging.DEBUG)


"""  The virtual font file format is as follows
Header:

PRE   VFID  comment     checksum    design size
247   202   k[l] x[k]   cs[4]       ds[4]

Font Definitions:
FNTDEF_N (1<=N<=4) number checksum  scalefactor  designsize  arealength filelength  area+file
242+N              k[N]   c[4]      s[4]         d[4]        a[1]       l[1]        n[a + l].

These are identical to the font definitions of a DVI file.  The scalefactor is interpreted
as a fixword relative to the design size of the VIRTUAL font.  The designsize of these
fonts seem to never be used.

Following the font definitions we have

Character Definitions: (two packet types, short or long)

SHORTCHAR_N (0<N<242)   char code  char width  dvi packet
N                       c[1]       tfm[3]      dvi[N]

LONGCHAR    packet length  char code    char width  div packet
243         pl[4]          c[4]         tfm[3]      dvi[pl]

At the end of the packets, there is a trival postamble, one or more bytes of

POST
248
"""

VFID = 202
LONGCHAR = 242
FNTDEF1 = 243
FNTDEF2 = 244
FNTDEF3 = 245
FNTDEF4 = 246
PRE = 247
POST = 248


# Structure for keeping all data associated with an individual virtual font character
class VFChar:
    def __init__(self, cc, width, dvi):
        self.cc = cc
        self.width = width
        self.dvi = dvi


# Exception for reporting errors reading a virtual font. Is there a more pythonic way
# to do this?
class VFFormatException(Exception):
    def __init__(self, msg):
        Exception.__init__(msg)


class VirtualFont:

    def __init__(self, vffile):
        import io

        self.vffile = vffile
        with open(self.vffile, "rb") as f:
            data = f.read()
        input = io.BytesIO(data)

        # The dictionary of fonts used by this virtual font.  The first one defined is the default
        self.fontTable = {}

        # Assume at least 256 characters for the font.
        self.packets = [None] * 256
        self.pcount = 0

        c1 = input.read(1)[0]
        c2 = input.read(1)[0]
        if (c1 != PRE) | (c2 != VFID):
            raise VFFormatException(
                "Invalid header for virtual font %s.\nExpecting %d %d, found %d %d."
                % vffile,
                PRE,
                VFID,
                c1,
                c2,
            )

        # Comment
        k = input.read(1)[0]
        self.comment = knuth.getString(input, k)

        # Checksum
        self.cs = knuth.getUnsigned(input, 4)

        # Design size
        self.ds = knuth.getUnsigned(input, 4)

        # Next comes a sequence of font definitions and character defs
        while True:
            c = input.read(1)[0]

            # Font Definitons
            if (FNTDEF1 <= c) & (c <= FNTDEF4):
                # In theory, all font defs occur first. Warn if this is not true.
                if self.pcount != 0:
                    logging.warning(
                        "Found a FNTDEF after the first char packet in a virtual font"
                    )
                m = c - 242
                k = knuth.getUnsigned(input, m)
                c = knuth.getUnsigned(input, 4)
                s = knuth.getUnsigned(input, 4)
                d = knuth.getUnsigned(input, 4)
                a = input.read(1)[0]
                ell = input.read(1)[0]
                fontfile = knuth.getString(input, ell)
                tf = DviFont.DviFont(fontfile, s, d, k)
                if len(self.fontTable) == 0:
                    self.defaultFont = tf
                self.fontTable["f" + str(tf.index)] = tf

            # Character packets
            elif c <= LONGCHAR:
                self.pcount += 1
                if c == LONGCHAR:
                    pl = knuth.getUnsigned(input, 4)
                    cc = knuth.getUnsigned(input, 4)
                else:
                    pl = c
                    cc = input.read(1)[0]
                width = knuth.getUnsigned(input, 3)
                dvi = input.read(pl)
                if cc >= len(self.packets):
                    self.packets.extend([None] * (cc + 1 - len(self.packets)))
                self.packets[cc] = VFChar(cc, width, dvi)

            # Postamble
            elif c == POST:
                break
            else:
                raise VFFormatException(
                    "Unknown opcode %d in virtual font %s" % c, vfname
                )

        input.close()


# if __name__ block commented out for now
