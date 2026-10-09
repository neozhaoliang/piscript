"""Cached lookups for TeX metrics, virtual fonts, fonts and map files."""

from piscript import FontMap, Type1
from piscript.kpsewhich import (
    ENC_TYPE,
    FONTMAP_TYPE,
    TFM_TYPE,
    TYPE1_TYPE,
    VF_TYPE,
    find,
)

vfPathCache = {}
tfmPathCache = {}
pfbPathCache = {}
type1Cache = {}
mapFileDict = {}


def _path(cache, name, kind):
    """Cache successful lookups only, allowing newly installed TeX files."""
    if name not in cache:
        path = find(name, kind)
        if path is not None:
            cache[name] = path
        return path
    return cache[name]


def getVF(name):
    return _path(vfPathCache, name, VF_TYPE)


def getTFM(name):
    return _path(tfmPathCache, name, TFM_TYPE)


def getPFB(name):
    return _path(pfbPathCache, name, TYPE1_TYPE)


def getEncoding(name):
    return find(name, ENC_TYPE)


def type1FontForPath(fontPath):
    if fontPath not in type1Cache:
        type1Cache[fontPath] = Type1.Type1Font(fontPath)
    return type1Cache[fontPath]


def getMapFile(name):
    if name in mapFileDict:
        return mapFileDict[name]
    path = find(name, FONTMAP_TYPE) or find(name + ".map", FONTMAP_TYPE)
    if path is None:
        return None
    map_file = FontMap.FontMap(path)
    mapFileDict[name] = map_file
    return map_file
