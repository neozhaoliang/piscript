import io
import piscript.FindResource as FindResource
from piscript.knuth import knuth

TFMCache = {}
VFCache = {}


class DviFont:
    def __init__(self, name, sf, d, index):
        self.fontName = name
        self.scaledSize = sf
        self.designSize = d
        self.index = index
        self.tfMetrics = None
        self.isUsed = False
        self.vChars = None
        self.isVirtual = False
        self.deviceFont = None

    def __str__(self):
        return f"DviFont {self.fontName} {self.designSize}"

    def getCharWidth(self, i):
        return self.tfMetrics.width[i]

    def getCharHeight(self, i):
        return self.tfMetrics.height[i]

    def getCharDepth(self, i):
        return self.tfMetrics.depth[i]

    def load(self):
        if self.fontName not in TFMCache:
            TFMCache[self.fontName] = TFMetrics(self.fontName)
        self.tfMetrics = TFMCache[self.fontName]


class TFMetrics:
    def __init__(self, fontfile):
        self.fontfile = fontfile
        tfm_path = FindResource.getTFM(fontfile)
        if tfm_path is None:
            raise FileNotFoundError(f"TFM file not found for font {fontfile}")
        tfm = Tfm(tfm_path)
        self.width = [0] * 256
        self.height = [0] * 256
        self.depth = [0] * 256
        scale = 1.0 / (1 << 20)
        for i in range(tfm.bc, tfm.ec + 1):
            self.width[i] = tfm.width[i] * scale
            self.height[i] = tfm.height[i] * scale
            self.depth[i] = tfm.depth[i] * scale


class Tfm:
    def __init__(self, fontname):
        with open(fontname, "rb") as f:
            data = f.read()
        input = io.BytesIO(data)

        (
            self.lf,
            self.lh,
            self.bc,
            self.ec,
            self.nw,
            self.nh,
            self.nd,
            self.ni,
            self.nl,
            self.nk,
            self.ne,
            _np,
        ) = (knuth.getInt(input, 2) for _ in range(12))
        self.readHeader(input)
        self.width = [0] * 256
        self.height = [0] * 256
        self.depth = [0] * 256
        self.readCharInfo(input)
        self._readCharDims(input, self.nw, "width", "wi")
        self._readCharDims(input, self.nh, "height", "hi")
        self._readCharDims(input, self.nd, "depth", "di")

    def toFixWord(self, n):
        return n * 1.0 / (1 << 20)

    def readHeader(self, input):
        self.chk = knuth.getWord(input)
        self.designSize = self.toFixWord(knuth.getWord(input))
        for _ in range(self.lh - 2):
            knuth.getWord(input)

    def readCharInfo(self, input):
        self.wi = [0] * self.bc
        self.hi = [0] * self.bc
        self.di = [0] * self.bc
        for _ in range(self.bc, self.ec + 1):
            charinfo = input.read(4)
            self.wi.append(charinfo[0])
            n = charinfo[1]
            self.hi.append(n >> 4)
            self.di.append(n & 15)

    def _readCharDims(self, input, count, attr, index_attr):
        w = [knuth.getInt(input, 4) for _ in range(count)]
        dims = [0] * 256
        for i in range(self.bc, self.ec + 1):
            dims[i] = w[getattr(self, index_attr)[i]]
        setattr(self, attr, dims)
