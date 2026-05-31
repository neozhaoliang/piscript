import logging
logger = logging.getLogger(__name__)
"""TeX runner and environment configuration.

Each Canvas has its own coordinate system + boundary and origin.
TexInserts have special points called marks.
"""

import os
import random
import subprocess

from piscript.DviToDevice import DviToDevice


class TexRunner:
    def __init__(self, texenv, texString, device, save=None, pin=False):
        self.texenv = texenv
        self.device = device
        self.string = texString
        self.label = save
        self.pinned = pin
        self.run()

    def run(self):
        if self.label is None:
            n = int(1024 * random.random())
            filename = "tmp" + str(n)
        else:
            filename = self.label
        self.filename = filename
        contents = self.texenv.prefix
        contents += "\n" + self.texenv.macros
        contents += "\n" + self.string
        contents += "\n" + self.texenv.postfix

        if self.label is None:
            self.tex(filename, contents)
        else:
            if os.path.exists(filename + ".tex") and os.path.exists(filename + ".dvi"):
                with open(filename + ".tex", "r", encoding="utf-8") as texin:
                    oldcontents = texin.read()
                if contents != oldcontents:
                    self.tex(filename, contents)
            else:
                self.tex(filename, contents)

        dvitodevice = DviToDevice(self.filename, self.device)
        dvitodevice.render()
        dvitodevice.input.close()

        if self.label is None:
            self.cleanup()

    def cleanup(self):
        filename = self.filename
        if self.label is None:
            for ext in [".tex", ".dvi"]:
                path = filename + ext
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass
        for ext in [".log", ".aux"]:
            path = filename + ext
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass

    def tex(self, filename, contents):
        with open(filename + ".tex", "w") as texout:
            texout.write(contents)

        cmd = self.texenv.command + " " + filename
        logger.info(f"TEX cmd = {cmd}")

        try:
            result = subprocess.run(
                [self.texenv.command, "-interaction=nonstopmode", filename],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
            )
            return result.returncode
        except FileNotFoundError:
            logger.error(f"TeX command '{self.texenv.command}' not found.")
            logger.error("Please install TeX Live or MiKTeX.")
            import sys
            sys.exit(1)
        except subprocess.TimeoutExpired:
            logger.warning(f"TeX command timed out for {filename}.tex")
            return 1


class TexEnv:
    def __init__(self, p, q, c):
        self.prefix = p
        self.macros = ""
        self.postfix = q
        self.command = c
        self.save = False

    def setprefix(self, s):
        self.prefix = s

    def setmacros(self, s):
        self.macros = s

    def setpostfix(self, s):
        self.postfix = s

    def setcommand(self, s):
        self.command = s

    def setsave(self, s):
        """s is True/False only."""
        self.save = s
