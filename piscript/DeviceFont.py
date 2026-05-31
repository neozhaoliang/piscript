"""DeviceFont — font lookup and management for PiScript."""

import piscript.Type1 as Type1
from piscript.EncodingVector import StandardEncodingVector, read_encoding, glyph_set_for_chars
from piscript.DviFont import TFMetrics
import piscript.FindResource as FindResource
import copy
from piscript.TexAliasDict import *
from piscript.TexFontNameDict import *
from piscript.CMRFontDict import cmrfontdict

import logging
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  DeviceFont base
# ---------------------------------------------------------------------------

class DeviceFont:
    def __init__(self, fontPath, embed=True, extract=True):
        self.fontPath = fontPath
        self.PSName = None
        self.shouldEmbed = embed
        self.shouldExtract = extract
        self.charNameList = set()
        self._charsUsed = [False] * 256
        self.glyphsUsed = set()

    def useChar(self, c):
        self._charsUsed[c] = True

    def useChars(self, cu):
        scu = self._charsUsed
        self._charsUsed = [cu[k] or scu[k] for k in range(256)]

    def charsUsed(self):
        return [k for k in range(256) if self._charsUsed[k]]

    def encodingVector(self):
        return list(StandardEncodingVector)

    def uniqueName(self):
        return self.PSName

    def type1Font(self):
        return None


# ---------------------------------------------------------------------------
#  Font variants
# ---------------------------------------------------------------------------

class PFBFont(DeviceFont):
    """A font backed by a .pfb file on disk."""

    def __init__(self, fontPath):
        DeviceFont.__init__(self, fontPath)
        self.PSName = FindResource.type1FontForPath(fontPath).fontName()

    def __str__(self):
        return f"PFBFont {self.PSName}:{self.fontPath}"

    def encodingVector(self):
        return FindResource.type1FontForPath(self.fontPath).encodingVector()

    def type1Font(self):
        return FindResource.type1FontForPath(self.fontPath)


class Base13Font(DeviceFont):
    """One of the 13 standard PostScript fonts — never embedded."""

    def __init__(self, fontName):
        DeviceFont.__init__(self, None)
        self.PSName = fontName
        self.shouldEmbed = False

    def __str__(self):
        return f"Base 13 Font {self.PSName}"

    def encodingVector(self):
        return list(StandardEncodingVector)


Base13Names = [
    "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
    "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique", "Symbol",
]

Base13Fonts = {k: Base13Font(k) for k in Base13Names}


class Font:
    """Associates a DeviceFont with a TeX name and point size."""

    __slots__ = ('font', 'name', 'size')

    def __init__(self, font, name, size):
        self.font = font
        self.name = name[1:] if name.startswith("/") else name
        self.size = size

    def texname(self):
        """Resolve the TeX font name through alias and fontname dicts."""
        name = self.name
        if name in aliasdict:
            return aliasdict[name]
        if name in texfontname:
            return texfontname[name]
        logger.warning(f"The font {name} cannot be found!")
        return None

    def metrics(self):
        return TFMetrics(self.texname())


class DeviceFontWithEncoding(DeviceFont):
    """Wraps a DeviceFont with a custom encoding vector."""

    def __init__(self, deviceFont, encoding, opts=None):
        DeviceFont.__init__(self, deviceFont.fontPath)
        self.deviceFont = deviceFont
        self.encodingFile = encoding
        self.opts = opts
        self.fullEncodingName = None

    def __str__(self):
        return f"FontWithEncoding {self.deviceFont}, {self.encodingFile}"

    def encodingVector(self):
        if self.encodingFile:
            encPath = FindResource.getEncoding(self.encodingFile)
            if encPath:
                try:
                    return read_encoding(encPath)
                except (OSError, ValueError, AttributeError):
                    pass
        return self.deviceFont.encodingVector()

    def type1Font(self):
        return self.deviceFont.type1Font()

    def uniqueName(self):
        if self.deviceFont is None:
            return None
        if self.encodingFile is None:
            return self.deviceFont.PSName
        return self.deviceFont.PSName + "-" + hex(hash(self.encodingFile))[2:]


# ---------------------------------------------------------------------------
#  FontTable
# ---------------------------------------------------------------------------

class FontTable:
    def __init__(self):
        self.deviceFonts = {}
        self.encodedFonts = {}
        self.mapNameToPSName = {}
        self.mapFile = (FindResource.getMapFile("dvipdfm")
                        or FindResource.getMapFile("pdftex")
                        or FindResource.getMapFile("psfonts"))
        self.aliasdict = aliasdict
        self.texfontname = texfontname

    def __str__(self):
        s = "WAC:FONT TABLEWAC:\nDevice Fonts:\n"
        for f in self.deviceFonts.values():
            s += f"  {f}\n"
        s += "EncodedFonts:\n"
        for f in self.encodedFonts.values():
            s += f"  {f}\n"
        return s

    def get(self, texName):
        return self.encodedFonts.get(texName)

    def getDeviceFont(self, psName):
        return self.deviceFonts.get(psName)

    def addDeviceFont(self, font):
        fontName = font.PSName
        currentFont = self.deviceFonts.get(fontName)
        if currentFont:
            return currentFont
        self.deviceFonts[fontName] = font
        return font

    def findFont(self, fontName):
        if fontName[0] == '/':
            fontName = fontName[1:]
        originalName = fontName

        if fontName in aliasdict:
            fontName = self.aliasdict[fontName]
        if fontName in texfontname:
            fontName = self.texfontname[fontName]

        f = (self._findLoadedFont(fontName)
             or self._findTeXFontCore(fontName)
             or self._findSystemFontCore(fontName))
        if f:
            return f

        if originalName != "Courier":
            logger.warning(f"Font {originalName} not found.  Using Courier.")
            return self.findFont("Courier")
        logger.warning("Fallback font Courier not found either.")
        return None

    def _findLoadedFont(self, fontName):
        return self.encodedFonts.get(fontName) or self.deviceFonts.get(fontName)

    def findSystemFont(self, fontName):
        return self._findLoadedFont(fontName) or self._findSystemFontCore(fontName)

    def _findSystemFontCore(self, fontName):
        deviceFont = Base13Fonts.get(fontName)
        if deviceFont:
            return self.addDeviceFont(deviceFont)
        texFontName = cmrfontdict.get(fontName)
        if texFontName:
            path = FindResource.getPFB(texFontName)
            if path:
                return PFBFont(path)

    def _findTeXFontCore(self, texFontName):
        if self.mapFile is None:
            return None
        mapEntry = self.mapFile.getEntry(texFontName)
        if mapEntry is None:
            return None
        psName = mapEntry.PSName
        if psName in self.mapNameToPSName:
            return self._makeEncodedFont(texFontName, mapEntry)
        deviceFont = Base13Fonts.get(psName)
        if deviceFont:
            return self.addDeviceFont(deviceFont)
        fontPath = FindResource.getPFB(psName)
        if not fontPath:
            logger.warning(f"Unable to find PFB file for font {psName}")
            return None
        deviceFont = self.addDeviceFont(PFBFont(fontPath))
        self.mapNameToPSName[psName] = deviceFont.PSName
        return self._makeEncodedFont(texFontName, mapEntry)

    def _makeEncodedFont(self, texFontName, mapEntry):
        psName = mapEntry.PSName
        font = DeviceFontWithEncoding(
            self.deviceFonts[psName], mapEntry.encoding, opts=mapEntry.opts)
        self.encodedFonts[texFontName] = font
        return font

    def merge(self, fontTable):
        for k, newFont in fontTable.encodedFonts.items():
            selfFont = self.encodedFonts.get(k)
            if selfFont:
                selfFont.useChars(newFont._charsUsed)
            else:
                psName = newFont.deviceFont.PSName
                selfDeviceFont = self.deviceFonts.get(psName)
                if selfDeviceFont:
                    newFont.deviceFont = selfDeviceFont
                    selfDeviceFont.useChars(newFont.deviceFont._charsUsed)
                else:
                    self.deviceFonts[psName] = newFont.deviceFont
                self.encodedFonts[k] = newFont
        self.mapNameToPSName.update(
            {k: v for k, v in fontTable.mapNameToPSName.items()
             if k not in self.mapNameToPSName})
