"""TeX resource finder with caching.

Looks up VF, TFM, Type1 fonts, encodings, and font maps
via matplotlib's kpathsea-backed find_tex_file.
"""

from piscript import FontMap
from piscript import Type1
from piscript.kpsewhich import find, VF_TYPE, TFM_TYPE, TYPE1_TYPE, ENC_TYPE, FONTMAP_TYPE

vfPathCache = {}


def getVF(fn):
    path = vfPathCache.get(fn)
    if not path:
        path = vfPathCache[fn] = find(fn, VF_TYPE)
    return path


tfmPathCache = {}


def getTFM(fn):
    path = tfmPathCache.get(fn)
    if not path:
        path = tfmPathCache[fn] = find(fn, TFM_TYPE)
    return path


type1Cache = {}


def type1FontForPath(fontPath):
    t1font = type1Cache.get(fontPath)
    if not t1font:
        t1font = type1Cache[fontPath] = Type1.Type1Font(fontPath)
    return t1font


pfbPathCache = {}


def getPFB(fn):
    path = pfbPathCache.get(fn)
    if not path:
        path = pfbPathCache[fn] = find(fn, TYPE1_TYPE)
    return path


def getEncoding(e):
    return find(e, ENC_TYPE)


mapFileDict = {}


def getMapFile(m):
    mf = mapFileDict.get(m)
    if not mf:
        p = find(m, FONTMAP_TYPE) or find(m + ".map", FONTMAP_TYPE)
        if not p:
            return None
        mf = mapFileDict[m] = FontMap.FontMap(p)
    return mf
