import re
"""
import logging
"""

"""dvipdfm fontmap entries are described in the dvipdfm user's manual.

  each entry is a line:

  texFontName encoding psFontName options

    texFontName corresponds with the TFM file name.

    encoding contains the name of a .enc file.
      If missing, or equal to 'default' or 'none', use the Type 1 font's encoding vector.

    psFontName contains either the file name of a Type 1 font, or a postscript font name.
      If missing, use texFontName.

    The options (which are all optional) are:
        -r (reencode to avoid control characters, something about a bug in Acrobat)
        -e number (extend font horizontally multiplying widths by 'number')
        -s number (slant the font by the given number)
"""

class FontMapEntry:
    def __init__(self, texFontName, encoding, PSName, opts ):
        self.texFontName = texFontName
        self.encoding = encoding
        # FIXME (DM 7/9/09) This is a misnomer.  
        # PSFontName  is really either the name of a file (a .pfb file?)
        #      or a base 13 font name.
        self.PSName = PSName
        if self.PSName == None:
            self.PSName = self.texFontName
        # Dictionary of character keys / values for the options
        self.opts = opts

    def __str__(self):
        return "FontMapEntry:%s (encoding %s) (PSFont %s) (opts %s)" % (self.texFontName, self.encoding, self.PSName, self.opts)

class FontMap:

    # When initially reading the font map, we just parse enough to determine which fonts are listed
    # the string that is the entry associated with each font.  When asked for a given font entry, we 
    # parse the entry and return a FontMapEntry
    
    def __init__( self, mapFilePath ):
        ### print "map file path =", mapFilePath
        self.mapFilePath = mapFilePath
        self.mapDict = {}
        # print "mapfile path", mapFilePath
        f = open(mapFilePath, "r", encoding="latin-1")
        mapFile = f.read()
        f.close()
        
        # Matches: #1:filename #2:other stuff.  We decode the other stuff later if need be.
        line_re=re.compile("^(\w[\w-]+)(?:[ \t]+(.+))?",re.M)
        lineIter = line_re.finditer(mapFile)
        for line in lineIter:
            g=line.groups()
            entry = g[1]
            if entry == None:
                entry = ""
            ### print "Font", g[0], ":", entry
            self.mapDict[g[0]] = entry

    def getEntry( self, texFontName ):
        mapEntry = self.mapDict.get( texFontName, None )
        ### print "me, fn", mapEntry, " ", texFontName
        if mapEntry == None:
            return None
#            logging.warning("Missing font map entry for %s in mapfile %s", texFontName, self.mapFilePath )
#            return FontMapEntry( texFontName, None, texFontName, None );
            
        entry_re = re.compile(r"(?:(\w[\w-]+))?(?:[ \t]+(\w[\w-]+))?(?:[ \t]+(.+))?")
        entry = entry_re.match(mapEntry)
        g = entry.groups()
        encoding = g[0]
        PSName = g[1]

        # pdftex.map format: PSName <file.pfb  (no encoding column)
        # dvipdfm format: encoding PSName <file.pfb
        # If the first field looks like a PS name and the second field
        # doesn't exist (starts with '<'), treat first field as PSName.
        if PSName is None and g[2] and g[2].strip().startswith('<'):
            PSName = encoding
            encoding = None

        if encoding in ("default", "none"):
            encoding = None

        if PSName is None:
            PSName = texFontName

        odict = {}
        if g[2] is not None:
            opt_re=re.compile("-([esr])(?:[ \t]+([-+]?(?:\d+(?:\.\d*)?|\.\d+)))?")
            olist = opt_re.findall(g[2])
            for opt in olist:
                odict[opt[0]] = opt[1]

        ### print "tex name, PSName =", texFontName, PSName
        return FontMapEntry( texFontName, encoding, PSName, odict )

if __name__ == "__main__":
    import sys
    fm = FontMap( sys.argv[1] )
    for f in fm.mapDict:
        print(fm.getEntry( f ))


