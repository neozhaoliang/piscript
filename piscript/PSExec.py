"""PostScript output engine — converts Canvas command arrays to .ps/.eps files."""

import re
import random
import os

from piscript.PSMatrix import concat as _mconcat, transform as _mtransform
import piscript.Fstr as Fstr
import piscript.PSReadable as PSReadable
import piscript.FindResource as FindResource
from piscript.DeviceFont import FontTable
from piscript.EncodingVector import glyph_set_for_chars
from piscript.Cmd import *

def float_to_hex(x):
    return f"{max(0, min(255, int(round(x * 255)))):02x}"


def pstrue(TF):
    return "true" if TF else "false"


savestr = ""
restorestr = ""

beginepsf = (
    "/BeginEPSF { "
    + savestr
    + " count /OpStackSize exch def /DictStackSize countdictstack def "
    "0 setgray 0 setlinecap 1 setlinewidth 0 setlinejoin "
    "10 setmiterlimit [] 0 setdash newpath } bind def\n"
)

endepsf = (
    "/EndEPSF { count OpStackSize sub dup 0 lt "
    "{neg {pop} repeat} {pop} ifelse countdictstack DictStackSize sub "
    "dup 0 lt {neg {end} repeat} {pop} ifelse " + restorestr + "} bind def\n"
)


class PSExec:

    def __init__(self):
        self.storagePath = "PiScript-tmp" + str(int(1024 * random.random())) + ".pys"
        self.storagefile = open(self.storagePath, "w", encoding="latin-1")
        self.fontTable = FontTable()
        self.pagecount = 0
        self.gsno = 0
        self._shfill_dispatch = {
            6: self._shfill_type6,
            4: self._shfill_type4,
            2: self._shfill_type2,
        }

        self.Command = [
            self.SetLineWidth,
            self.SetLineCap,
            self.SetLineJoin,
            self.SetDash,
            self.SetMiterLimit,
            self.SetColor,
            self.ScaleLineWidth,
            self.Newpath,
            self.Moveto,
            self.Lineto,
            self.Curveto,
            self.Fill,
            self.Stroke,
            self.CFill,
            self.CStroke,
            self.Clip,
            self.SetFont,
            self.Show,
            self.Embed,
            self.Closepath,
            self.Insert,
            self.PSImport,
            self.EPSImport,
            self.GSave,
            self.GRestore,
            self.SHFill,
            self.Comment,
            self.Embed_image,
        ]

    def setbbox(self, bbox):
        self.bbox = bbox

    # ---- output buffering ----

    def psadd(self, ps):
        if len(self.ps) > 10000:
            self.storagefile.write(self.ps)
            self.storagefile.flush()
            self.ps = ""
        self.ps += ps

    # ---- page management ----

    def writePage(self, insert):
        self._beginpage()
        self.fontTable.merge(insert.fontTable)
        self.execute(insert.cmd, [1, 0, 0, 1, 0, 0])
        self._endpage()
        self.storagefile.write(self.ps)
        self.storagefile.flush()

    def execute(self, cmd, matrix):
        n = len(cmd)
        i = 0
        while i < n:
            c = cmd[i]
            self.Command[c](cmd, i, matrix)
            i += Skip[c]

    def _beginpage(self):
        self.gsno = 0
        self.pagecount += 1
        self.ps = "%%Page: " + str(self.pagecount) + " " + str(self.pagecount) + "\n"

    def _endpage(self):
        for _ in range(self.gsno):
            self.psadd("grestore ")
        self.psadd("showpage\n")
        self.psadd("\n% ---------------------------------------------------------\n\n")

    # ---- graphics state commands ----

    def GSave(self, cmd, i, m):
        self.gsno += 1
        self.psadd("gsave\n")

    def GRestore(self, cmd, i, m):
        self.gsno -= 1
        self.psadd("grestore\n")

    def SetLineWidth(self, cmd, i, m):
        self.psadd(Fstr.fstr(cmd[i + 1]) + " setlinewidth\n")

    def SetLineCap(self, cmd, i, m):
        self.psadd(str(cmd[i + 1]) + " setlinecap\n")

    def SetLineJoin(self, cmd, i, m):
        self.psadd(str(cmd[i + 1]) + " setlinejoin\n")

    def SetMiterLimit(self, cmd, i, m):
        self.psadd(Fstr.fstr(cmd[i + 1]) + " setmiterlimit\n")

    def SetDash(self, cmd, i, m):
        a = cmd[i + 1]
        o = cmd[i + 2]
        ps = "[" + " ".join(str(x) for x in a) + "] " + str(o) + " setdash\n"
        self.psadd(ps)

    def SetColor(self, cmd, i, m):
        r, g, b = cmd[i + 1], cmd[i + 2], cmd[i + 3]
        self.psadd(f"{Fstr.fstr(r)} {Fstr.fstr(g)} {Fstr.fstr(b)} setrgbcolor\n")

    def ScaleLineWidth(self, cmd, i, m):
        self.psadd("currentlinewidth " + Fstr.fstr(cmd[i + 1]) + " mul setlinewidth\n")

    # ---- path construction ----

    def Newpath(self, cmd, i, m):
        self.psadd("newpath\n")

    def Moveto(self, cmd, i, m):
        x, y = _mtransform(m, cmd[i + 1], cmd[i + 2])
        self.psadd(f"{Fstr.fstr(x)} {Fstr.fstr(y)} moveto\n")

    def Lineto(self, cmd, i, m):
        x, y = _mtransform(m, cmd[i + 1], cmd[i + 2])
        self.psadd(f"{Fstr.fstr(x)} {Fstr.fstr(y)} lineto\n")

    def Curveto(self, cmd, i, m):
        points = []
        for j in range(3):
            x, y = _mtransform(m, cmd[i + 1 + j * 2], cmd[i + 2 + j * 2])
            points.append(f"{Fstr.fstr(x)} {Fstr.fstr(y)}")
        self.psadd(" ".join(points) + " curveto\n")

    def Closepath(self, cmd, i, m):
        self.psadd("closepath\n")

    # ---- fill / stroke ----

    def Fill(self, cmd, i, m):
        self.psadd("gsave fill grestore\n")

    def Stroke(self, cmd, i, m):
        self.psadd("gsave stroke grestore\n")

    def CFill(self, cmd, i, m):
        self._color_fill_stroke(cmd, i, "fill")

    def CStroke(self, cmd, i, m):
        self._color_fill_stroke(cmd, i, "stroke")

    def _color_fill_stroke(self, cmd, i, op):
        r, g, b = cmd[i + 1], cmd[i + 2], cmd[i + 3]
        self.psadd(
            f"gsave\n{Fstr.fstr(r)} {Fstr.fstr(g)} {Fstr.fstr(b)} setrgbcolor\n{op}\ngrestore\n"
        )

    def Clip(self, cmd, i, m):
        self.psadd("clip\n")

    # ---- text ----

    def SetFont(self, cmd, i, m):
        self.psadd(f"/{cmd[i + 1]} findfont\n{cmd[i + 2]} scalefont\nsetfont\n")

    def Show(self, cmd, i, m):
        tm = _mconcat(cmd[i + 2], m)
        outString = "".join(PSReadable.toReadable[c] for c in cmd[i + 1])
        self.psadd("gsave\n[ ")
        for k in range(6):
            self.psadd(" " + str(tm[k]))
        self.psadd(" ] concat\n")
        self.psadd("(" + outString + ") show\n")
        self.psadd("grestore\n")

    # ---- embedding ----

    def Embed(self, cmd, i, m):
        c = cmd[i + 1]
        m = _mconcat(m, c.m)
        self.execute(c.cmd, m)

    def Insert(self, cmd, i, m):
        self.psadd("% --- raw inclusion --- \n")
        self.psadd(cmd[i + 1])
        self.psadd("% --- end of inclusion --- \n")

    def PSImport(self, cmd, i, m):
        eps = cmd[i + 1]
        tm = _mconcat(cmd[i + 2], m)
        self.psadd("[ ")
        for k in range(6):
            self.psadd(" " + str(tm[k]))
        self.psadd(" ] concat\n")
        self.psadd("%% --- inserting file " + eps + " --- \n")
        with open(eps, "rb") as f:
            self.psadd(f.read())
        self.psadd("%% --- end of insert " + eps + " --- \n")

    # ---- EPS import ----

    def EPSImport(self, cmd, i, m):
        eps = cmd[i + 1]
        tm = _mconcat(cmd[i + 2], m)
        with open(eps, "rb") as f:
            F = f.read()
        self.EPSinclude(F, tm)

    def EPSinclude(self, F, tm):
        self.psadd("gsave\n[ ")
        for k in range(6):
            self.psadd(" " + str(tm[k]))
        self.psadd(" ] concat\n")
        self.psadd("1 dict begin\n")
        self.psadd(endepsf)
        self.psadd(beginepsf)
        self.psadd("/showpage{} def\n")
        self.psadd("BeginEPSF\n")
        self.psadd("%%BeginDocument:\n")
        self.psadd(F)
        self.psadd("%%EndDocument\n")
        self.psadd("EndEPSF\n")
        self.psadd("end\n")
        self.psadd("grestore\n")

    # ---- image ----

    def Embed_image(self, cmd, i, m):
        img = cmd[i + 1]
        n = cmd[i + 2]
        interpolate = cmd[i + 3]
        ctm = cmd[i + 4]
        h = len(img)
        w = len(img[0])
        s = "/DeviceRGB setcolorspace\n"
        s += "[ " + " ".join(str(ctm[j]) for j in range(6)) + " ] concat\n"
        s += "<<\n"
        s += f"/ImageType 1\n/Width {w}\n/Height {h}\n"
        s += "/BitsPerComponent 8\n/Decode [ 0 1 0 1 0 1 ]\n"
        s += f"/ImageMatrix [ {n} 0 0 {n} 0 0 ]\n"
        s += f"/Interpolate {pstrue(interpolate)}\n"
        s += "/DataSource currentfile /ASCIIHexDecode filter\n>>\nimage\n"
        for row in img:
            for r, g, b in row:
                s += float_to_hex(r) + float_to_hex(g) + float_to_hex(b)
            s += "\n"
        s += ">\n"
        self.psadd(s)

    # ---- shading ----

    def SHFill(self, cmd, i, m):
        self._shfill_dispatch[cmd[i + 1]](cmd[i + 2])

    def _shfill_type6(self, ds):
        parts = ["0"] + [Fstr.fstr(x) for x in ds]
        self.psadd("\nnewpath\n<<\n/ShadingType 6\n")
        self.psadd("/ColorSpace [ /DeviceRGB ]\n/DataSource [\n")
        self.psadd(" ".join(parts) + " \n]\n>>\nshfill\n\n")

    def _shfill_type4(self, ds):
        self.psadd("\nnewpath\n<<\n/ShadingType 4\n")
        self.psadd("/ColorSpace [ /DeviceRGB ]\n/DataSource [\n")
        for triangle in ds:
            for P, C in triangle:
                self.psadd(
                    f"0 {Fstr.fstr(P[0])} {Fstr.fstr(P[1])} "
                    f"{Fstr.fstr(C[0])} {Fstr.fstr(C[1])} {Fstr.fstr(C[2])}\n"
                )
        self.psadd("]\n>>\nshfill\n\n")

    def _shfill_type2(self, ds):
        x0, y0, x1, y1 = ds[0], ds[1], ds[2], ds[3]
        C0, C1 = ds[7:10], ds[4:7]
        self.psadd("\nnewpath\n<<\n/ShadingType 2\n/ColorSpace /DeviceRGB\n")
        self.psadd(
            f"/Coords [ {Fstr.fstr(x1)} {Fstr.fstr(y1)} "
            f"{Fstr.fstr(x0)} {Fstr.fstr(y0)} ]\n"
        )
        self.psadd("/Function <<\n\t/FunctionType 2\n\t/Domain [ 0 1 ]\n")
        self.psadd(
            f"\t/C0 [ {Fstr.fstr(C0[0])} {Fstr.fstr(C0[1])} {Fstr.fstr(C0[2])} ]\n"
        )
        self.psadd(
            f"\t/C1 [ {Fstr.fstr(C1[0])} {Fstr.fstr(C1[1])} {Fstr.fstr(C1[2])} ]\n"
        )
        self.psadd("/N 1\n>>\n>>\nshfill\n\n")

    # ---- comment ----

    def Comment(self, cmd, i, m):
        self.psadd("\n% Comment: " + cmd[i + 1] + "\n\n")

    # ---- bounding box / finish ----

    @staticmethod
    def epsboundingbox(filename):
        with open(filename, "rb") as f:
            for line in f:
                m = re.search(
                    r"%%BoundingBox:[ ]+([0-9]+)[ ]+([0-9]+)[ ]+([0-9]+)[ ]+([0-9]+)",
                    line,
                )
                if m:
                    return [
                        int(m.group(1)),
                        int(m.group(2)),
                        int(m.group(3)),
                        int(m.group(4)),
                    ]
                if "%%BoundingBox:[ ]+(\(atend\))" in line:
                    depth = 0
                    for line in f:
                        if "%%BeginDocument" in line:
                            depth += 1
                        if "%%EndDocument" in line:
                            depth -= 1
                        if "%%Trailer" in line and depth == 0:
                            break
            return None

    @staticmethod
    def roundBBox(a, b):
        import math

        if a < b:
            return (math.floor(a), math.ceil(b))
        return (math.ceil(a), math.floor(b))

    def finish(self, outFile, toEPS=True):
        self.storagefile.close()
        self.storagefile = open(self.storagePath, "r", encoding="latin-1")

        header = "%!PS-Adobe-2.0 EPSF-3.0\n" if toEPS else "%!PS-Adobe-2.0\n"
        llx, lly, urx, ury = self.bbox
        llx, urx = self.roundBBox(llx, urx)
        lly, ury = self.roundBBox(lly, ury)
        header += f"%%BoundingBox: {int(llx)} {int(lly)} {int(urx)} {int(ury)}\n"
        header += f"%%Pages: {self.pagecount}\n%%PageOrder: Ascend\n\n"
        header += "%%BeginProlog\n"
        header += "%%BeginProcSet: \n"
        header += "/ReEncodeFont { exch findfont << >> copy dup 3 2 roll "
        header += "/Encoding exch put definefont } def\n"
        header += "%%EndProcSet\n"
        outFile.write(header)

        for deviceFont in self.fontTable.deviceFonts.values():
            deviceFont.glyphsUsed = glyph_set_for_chars(
                deviceFont.encodingVector(), deviceFont.charsUsed())

        for encodedFont in self.fontTable.encodedFonts.values():
            encodedGlyphsUsed = glyph_set_for_chars(
                encodedFont.encodingVector(), encodedFont.charsUsed())
            encodedFont.deviceFont.glyphsUsed.update(encodedGlyphsUsed)

        encodings = set(
            encFont.encodingFile
            for encFont in self.fontTable.encodedFonts.values()
            if encFont.encodingFile
        )

        encodingNames = {}
        for e in encodings:
            encodingNames[e] = self.emitEncoding(e, outFile)

        for f in self.fontTable.deviceFonts.values():
            if not f.shouldEmbed or not f.fontPath:
                continue
            t = FindResource.type1FontForPath(f.fontPath)
            if f.shouldExtract:
                fout = t.extractPFA(f.glyphsUsed)
            else:
                fout = t.toPFA()
            outFile.write("%%BeginFont: " + f.PSName + "\n")
            outFile.write(fout)
            outFile.write("%%EndFont " + f.PSName + "\n")

        outFile.write("%%EndProlog\n")

        for f in self.fontTable.encodedFonts.values():
            if f.encodingFile is None:
                continue
            fullEncodingName = encodingNames.get(f.encodingFile)
            if fullEncodingName is None:
                outFile.write(
                    f"/{f.uniqueName()} /{f.deviceFont.PSName}"
                    f" findfont definefont pop\n"
                )
            else:
                outFile.write(
                    f"/{f.uniqueName()} /{f.deviceFont.PSName} "
                    f"{fullEncodingName} ReEncodeFont\n"
                )

        outFile.flush()

        outFile.write(self.storagefile.read())
        self.storagefile.close()
        os.remove(self.storagePath)

        outFile.write("%%Trailer\n%%EOF\n")

    def emitEncoding(self, encodingFile, out):
        encPath = FindResource.getEncoding(encodingFile)
        if encPath is None:
            return None

        with open(encPath, "r", encoding="latin-1") as encFile:
            out.write(f"%%%%BeginProcSet: {encodingFile} 0 0\n")
            encName = None
            name_re = re.compile(r"^\s*/(\w+)\s.*")
            for line in encFile:
                if encName is None:
                    m = name_re.match(line)
                    if m:
                        encName = m.group(1)
                out.write(line)
            out.write("%%EndProcSet\n")
            return encName
