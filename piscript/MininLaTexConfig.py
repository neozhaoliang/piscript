"""LaTeX config with MinionPro font."""

import shutil

from piscript.Tex import TexEnv

fontPackage = "MinionPro"


def getTexEnv():
    cmd = shutil.which("latex") or shutil.which("pdflatex") or "latex"
    p = "\\documentclass[12pt]{article}\n"
    p += f"\\usepackage{{{fontPackage}}}\n"
    p += "\\pagestyle{empty}\n"
    p += "\\input amssym.def\n"
    p += "\\newcommand\\color[1]{\\special{Color{#1}}}\n"
    p += "\\newcommand\\uncolor{\\special{unColor}}\n"
    p += "\\newcommand\\lmark{\\special{mark}}\n"
    p += "\\begin{document}\n"
    q = "\n%\n\\end{document}\n"
    return TexEnv(p, q, cmd)
