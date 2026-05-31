"""Plain TeX config with boldmathfont.defs."""

import shutil

from piscript.Tex import TexEnv


def getTexEnv():
    cmd = shutil.which("tex") or shutil.which("pdftex") or "tex"
    p = "\\input amssym.def\n"
    p += "\\def\\color#1{\\special{color{#1}}}\n"
    p += "\\def\\uncolor{\\special{uncolor}}\n"
    p += "\\def\\mark{\\special{mark}}\n"
    p += "\\nopagenumbers\n"
    p += "\\input boldmathfont.defs\n"
    q = "\n%\n\\bye\n"
    return TexEnv(p, q, cmd)
