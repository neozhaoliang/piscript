"""Run TeX to create DVI-backed text inserts for PiScript."""

import logging
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

from piscript.DviToDevice import DviToDevice

logger = logging.getLogger(__name__)


class TexRunner:
    """Compile text in a TeX environment and render its DVI into a device."""

    def __init__(self, texenv, texString, device, save=None, pin=False):
        self.texenv = texenv
        self.device = device
        self.string = texString
        self.label = save
        self.pinned = pin
        self.run()

    def run(self):
        if self.label is None:
            fd, path = tempfile.mkstemp(prefix="piscript-", suffix=".tex", dir=".")
            os.close(fd)
            self.filename = str(Path(path).with_suffix(""))
        else:
            self.filename = os.fspath(self.label)

        tex_path = Path(self.filename + ".tex")
        dvi_path = Path(self.filename + ".dvi")
        contents = "\n".join((
            self.texenv.prefix, self.texenv.macros,
            self.string, self.texenv.postfix,
        ))
        try:
            if (not tex_path.exists() or not dvi_path.exists()
                    or tex_path.read_text(encoding="utf-8") != contents):
                self.tex(self.filename, contents)
            if not dvi_path.is_file():
                raise RuntimeError(
                    f"TeX did not produce a DVI file: {dvi_path}. "
                    "Use a DVI-producing engine such as latex."
                )
            reader = DviToDevice(self.filename, self.device)
            try:
                reader.render()
            finally:
                reader.input.close()
        finally:
            if self.label is None:
                self.cleanup()

    def cleanup(self):
        """Remove temporary source/output, keeping saved documents."""
        extensions = (".log", ".aux")
        if self.label is None:
            extensions += (".tex", ".dvi")
        for suffix in extensions:
            try:
                Path(self.filename + suffix).unlink(missing_ok=True)
            except OSError as error:
                logger.warning("Could not remove TeX file: %s", error)

    def tex(self, filename, contents):
        tex_path = Path(filename + ".tex")
        tex_path.write_text(contents, encoding="utf-8")
        command = shlex.split(self.texenv.command)
        if not command:
            raise ValueError("TeX executable is not configured")
        args = [*command, "-interaction=nonstopmode", tex_path.name]
        logger.debug("Running TeX: %s (in %s)", args, tex_path.parent)
        try:
            result = subprocess.run(
                args, cwd=tex_path.parent, capture_output=True,
                text=True, errors="replace", timeout=60, check=False,
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                f"TeX command '{command[0]}' not found; install TeX Live or MiKTeX"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f"TeX compilation timed out: {tex_path}") from error
        if result.returncode:
            raise RuntimeError(
                f"TeX compilation failed for {tex_path} "
                f"(exit code {result.returncode}):\n{result.stdout[-2000:]}"
            )
        return result.returncode


class TexEnv:
    """Mutable TeX preamble, postfix and compiler configuration."""

    def __init__(self, p, q, c):
        self.prefix = p
        self.macros = ""
        self.postfix = q
        self.command = c
        self.save = False

    def setprefix(self, value):
        self.prefix = value

    def setmacros(self, value):
        self.macros = value

    def setpostfix(self, value):
        self.postfix = value

    def setcommand(self, value):
        self.command = value

    def setsave(self, value):
        self.save = bool(value)
