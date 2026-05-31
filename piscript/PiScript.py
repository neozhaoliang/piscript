#!/usr/bin/env python3

import math
import os
import sys

from piscript.Canvas import Canvas
from piscript.DeviceFont import FontTable  # noqa: used implicitly
from piscript.DviReader import *  # noqa: used implicitly
import numpy as np
from piscript.Tex import TexEnv, TexRunner
from piscript.PysCmdDevice import PysCmdDevice
from piscript.VectorUtils import Vector  # noqa: re-exported via PiModule


import logging
logger = logging.getLogger(__name__)
class PageData:
    """Stores a snapshot of canvas commands and graphics stack level."""

    def __init__(self, cmd, level):
        self.cmd = list(cmd)
        self.level = level


class PiScript(Canvas):
    """Main PiScript engine - builds canvas and produces PostScript output.

    Usage:
        ps = PiScript(PSExec(), 300, 200)   # w=300, h=200, auto filename
        ps = PiScript(PSExec(), "output", 300, 200)  # explicit filename
        ps = PiScript(PSExec(), "output.ps", 300, 200)  # .ps extension
    """

    def __init__(self, device, *args):
        args = list(args)
        cliptobbox = True
        if args and isinstance(args[-1], str) and args[-1] == "noclip":
            cliptobbox = False
            args.pop()

        if not args:
            logger.error("No arguments for init!")
            logger.error("Exiting ... ")
            sys.exit(1)

        # Parse filename, extension, and bounding box from args
        filename, ext, llx, lly, urx, ury = self._parse_args(args)

        Canvas.__init__(self)
        self.bbox = [llx, lly, urx, ury]

        logger.info(f"Initializing {filename}{ext}")
        self.filename = filename
        self.ext = ext
        self.device = device

        w = urx - llx
        h = ury - lly
        self.width = w
        self.height = h
        device.setbbox([llx, lly, urx, ury])

        self.settexenv("TexConfig")
        self.insertno = 0

        self.pageno = 0
        self.pagestring = ""
        self.pagestack = [PageData([], self.glevel)]
        self.beginpage()

        if cliptobbox:
            self.newpath()
            self.boundedbox(self.bbox)
            self.clip()

        self.lablist = []
        self.endblock = True

    def _parse_args(self, args):
        """Parse init arguments: filename, extension, and bounding box."""
        ext = ".eps"
        main_file = sys.modules.get('__main__', None)
        pyfile = getattr(main_file, '__file__', 'output')

        if isinstance(args[0], str):
            a = args[0]
            if a in (".ps", ".eps"):
                ext = a
                filename = pyfile[:-3] if pyfile.endswith(".py") else pyfile
            elif a.endswith(".ps"):
                filename = a[:-3]
                ext = ".ps"
            elif a.endswith(".eps"):
                filename = a[:-4]
                ext = ".eps"
            else:
                filename = a
            bbox_args = args[1:]
        else:
            if not pyfile.endswith(".py"):
                logger.error("Expecting source file with .py extension")
                logger.error("Exiting ... ")
                sys.exit(1)
            filename = pyfile[:-3]
            bbox_args = args

        if len(bbox_args) == 2:
            llx, lly, urx, ury = 0, 0, int(bbox_args[0]), int(bbox_args[1])
        elif len(bbox_args) == 4:
            llx, lly, urx, ury = (int(x) for x in bbox_args)
        else:
            logger.error("Expected 2 or 4 numeric args for dimensions")
            sys.exit(1)

        return filename, ext, llx, lly, urx, ury

    # =================================================================

    def currentcenter(self):
        gs = self.cgs()
        b = self.bbox
        x = 0.5 * (b[0] + b[2])
        y = 0.5 * (b[1] + b[3])
        return gs.transform((x, y))

    def currentbbox(self):
        b = self.bbox
        gs = self.cgs()
        return [
            gs.transform((b[0], b[1])),
            gs.transform((b[2], b[1])),
            gs.transform((b[2], b[3])),
            gs.transform((b[0], b[3])),
        ]

    def center(self):
        b = self.bbox
        x = 0.5 * (b[0] + b[2])
        y = 0.5 * (b[1] + b[3])
        self.translate(x, y)

    def beginpage(self, *args):
        self.pagestring += "("
        opd = self.pagestack[-1]
        pd = PageData(opd.cmd, opd.level)
        self.pagestack.append(pd)
        self.cmd = pd.cmd
        self.gsave()

    def endpage(self):
        n = len(self.pagestack)
        if self.endblock and n == 2:
            logger.error("finish() called before endpage()")
            logger.error("Now exiting ...")
            sys.exit(1)

        ell1 = self.glevel
        ell0 = self.baselevel() + 1
        ell = ell1 - ell0
        if ell != 0:
            if ell < 0:
                logger.warning("There is an extra grestore!")
            elif ell > 1:
                logger.warning(f"There are {ell} too many gsaves!")
            else:
                logger.warning("There is an extra gsave!")
            logger.info("Restoring to default coordinates!")
        for _ in range(ell + 1):
            self.grestore()

        if self.pagestring[-1] == "(":
            self.device.writePage(self)
            self.pageno += 1
            logger.info(f"[{self.pageno}]")
        self.pagestring += ")"
        self.pagestack.pop()
        pd = self.pagestack[-1]
        self.cmd = pd.cmd

    @staticmethod
    def inv(M):
        d = float(M[0] * M[3] - M[1] * M[2])
        return (M[3] / d, -M[1] / d, -M[2] / d, M[0] / d)

    @staticmethod
    def Transform(M, P):
        return (M[0] * P[0] + M[1] * P[1], M[2] * P[0] + M[3] * P[1])

    def finish(self):
        self.endblock = False
        self.endpage()

        if self.lablist:
            with open(self.filename + ".lab", "w", encoding="utf-8") as labelfile:
                for ell in self.lablist:
                    string = ell[0]
                    matrix = ell[1]
                    location = ell[2]
                    origin = ell[3]

                    M = [[matrix[0], matrix[2]], [matrix[1], matrix[3]]]
                    U, s, Vh = np.linalg.svd(M)
                    A1 = math.atan2(U[1, 0], U[0, 0])
                    A1 = (180.0 / math.pi) * A1
                    R1 = f"\\RotateBox{{{A1!s}}}"

                    A2 = math.atan2(Vh[1, 0], Vh[0, 0])
                    A2 = (180.0 / math.pi) * A2
                    R2 = f"\\RotateBox{{{A2!s}}}"

                    S = f"\\scalebox{{{s[0]}}}[{s[1]}]"
                    matrixstr = R1 + "{" + S + "{" + R2 + "{" + str(ell[0]) + "}}}"

                    o0, o1 = PiScript.Transform(M, (origin[0], origin[1]))
                    x = matrix[4] + o0
                    y = matrix[5] + o1
                    location[0] += x
                    location[1] += y

                    label = matrixstr + " [Bl] at " + str((72.27 / 72) * location[0]) + " " + str((72.27 / 72) * location[1]) + "\n"
                    labelfile.write("\\pinlabel* " + label)
        else:
            lab_path = self.filename + ".lab"
            if os.path.exists(lab_path):
                os.remove(lab_path)

        with open(self.filename + self.ext, "w", encoding="latin-1") as finalout:
            self.device.finish(finalout, toEPS=(self.ext == '.eps'))

    def baselevel(self):
        opd = self.pagestack[-2]
        return opd.level

    def gsave(self):
        pd = self.pagestack[-1]
        pd.level += 1
        Canvas.gsave(self)

    def grestore(self):
        ell0 = self.baselevel()
        ell1 = self.glevel
        if ell1 > ell0:
            Canvas.grestore(self)
            pd = self.pagestack[-1]
            pd.level -= 1
        else:
            logger.warning("too many grestores!")

    # === TeX configuration ===

    def settexprefix(self, s):
        self.texenv.setprefix(s)

    def settexmacros(self, s):
        self.texenv.setmacros(s)

    def settexpostfix(self, s):
        self.texenv.setpostfix(s)

    def settexcommand(self, s):
        self.texenv.setcommand(s)

    def settexsave(self, save):
        self.texenv.setsave(save)

    def settexenv(self, *args):
        logger.info(f"TEX = {args[0]}")
        if len(args) == 1:
            arg = args[0]
            if arg == "plain":
                cfgfile = "PlainTexConfig"
            elif arg == "latex":
                cfgfile = "LaTexConfig"
            else:
                cfgfile = arg

            cfg = self._find_tex_config(cfgfile)
            if cfg is None:
                logger.warning(f"TEX configuration {cfgfile} not found!")
                logger.warning(f"checked: {os.path.join(os.getcwd(), cfgfile + '.py')}")
                logger.error("Aborting due to missing TEX configuration")
                sys.exit(1)
        else:
            self.texenv = TexEnv(*args)

    def _find_tex_config(self, cfgfile):
        """Search for a TeX config file in standard locations."""
        search_paths = [
            os.path.join(os.getcwd(), cfgfile + ".py"),
        ]
        if "LOCALPISCRIPTDIR" in os.environ:
            local = os.environ["LOCALPISCRIPTDIR"]
            local = local.replace("$HOME", os.path.expanduser("~"))
            search_paths.append(os.path.join(local, "configs", cfgfile + ".py"))
        search_paths.append(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), cfgfile + ".py")
        )

        for cfgpathname in search_paths:
            if os.path.exists(cfgpathname):
                return self._load_tex_config(cfgpathname)
        return None

    def _load_tex_config(self, cfgpathname):
        logger.info(f"importing {cfgpathname}")
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "piscript_tex_cfg", cfgpathname)
        cfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cfg)
        self.texenv = cfg.getTexEnv()
        return self.texenv

    def settexconfig(self, texcfg):
        """Set TeX configuration. Same arguments as settexenv."""
        self.settexenv(texcfg)

    def stringinsert(self, s):
        from piscript.StringInsert import StringInsert
        return StringInsert(s)

    def texinsert(self, texstring, save=None, pin=False):
        import copy
        if not hasattr(self, '_texinsert_cache'):
            self._texinsert_cache = {}
        cache_key = (texstring, save is not None, pin)
        if cache_key in self._texinsert_cache:
            return copy.deepcopy(self._texinsert_cache[cache_key])
        if save:
            import os
            base = os.path.splitext(os.path.basename(self.filename))[0]
            save = f"tmp-{base}-{self.insertno}"
            self.insertno += 1
        tr = TexRunner(
            self.texenv, texstring,
            PysCmdDevice(792, self.currentcolor()),
            save=save,
        )
        T = tr.device.pages[0]
        T.pinned = pin
        T.texstring = texstring
        self._texinsert_cache[cache_key] = copy.deepcopy(T)
        return copy.deepcopy(T)

    def _flush_texinserts(self):
        pass

    def place(self, canvas, *args):
        s = Canvas.place(self, canvas, *args)
        if s:
            if not args:
                P = (0, 0)
            elif len(args) == 1:
                P = args[0]
            else:
                P = (args[0], args[1])
            gs = self.cgs()
            v = gs.transform(P)
            m = list(canvas.m)
            origin = list(canvas.origorigin)
            self.lablist.append([s, m, v, origin])

    def minx(self):
        return self.bbox[0]

    def maxx(self):
        return self.bbox[2]

    def miny(self):
        return self.bbox[1]

    def maxy(self):
        return self.bbox[3]
