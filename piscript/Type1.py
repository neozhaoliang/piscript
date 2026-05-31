import logging
import re
import piscript.AsciiHex as AsciiHex
from piscript.EncodingVector import StandardEncodingVector
import logging
logger = logging.getLogger(__name__)
isWhiteSpace = [ False ] *256
isWhiteSpace[ord('\n')] = True
isWhiteSpace[ord('\r')] = True
isWhiteSpace[ord('\t')] = True
isWhiteSpace[ord(' ')] = True

PFA_TYPE = 0
PFB_TYPE = 1

def lowEndian(s):
    import struct
    return struct.unpack("<I", s[:4])[0]

def fontNameFromPath( fontPath ):
    f = Type1Font( fontPath )
    return f.fontName()

class Type1Font:
    def __init__( self, fontPath ):
        self.fontPath = fontPath
        self.fontFile = open( fontPath, "rb" );
        c = self.fontFile.read(1)
        if c == b'\x80':
            self.type = PFB_TYPE
            self.partitionPFB()
        elif c == b'%':
            self.type = PFA_TYPE
            self.partitionPFA()
        else:
            raise OSError(
                f"Unrecognized font format in {fontPath}: "
                f"expected PFB (starting with 0x80) or PFA (starting with %)"
            )
        self.aPart = None
        self.bPart = None

    def __str__( self ):
        print("\n ---- calling font string --- \n")
        return str(self.asciiPart()) + str(self.binaryPart()) + self.zeroPart()

    def __del__( self ):
        if hasattr(self, 'fontFile'):
            self.fontFile.close()

    def fontName( self ):
        return self.asciiPart().fontName()

    def fontMatrix( self ):
        return self.asciiPart().fontMatrix()

    def encodingVector( self ):
        a = self.asciiPart()
        return a.encodingVector

    def charStrings( self ):
        return self.binaryPart().charStrings()

    # both the next two return a CharString
    def charStringForChar( self, c, encoding = None ):
        if encoding == None:
            encoding = self.encodingVector()
        glyphName = encoding[c]
        return self.binaryPart().charStringForGlyph( glyphName )
        
    def charStringForGlyph( self, glyphName ):
        return self.binaryPart().charStringForGlyph( glyphName )
                
    def subroutines( self ):
        return self.binaryPart().subroutines()

    def subroutine( self, index):
        return self.binaryPart().subroutine( index )
        
    def toPFA( self ):
        # We are already PFA, this is easy!
        if self.type == PFA_TYPE:
            self.fontFile.seek(0)
            return self.fontFile.read()
        
        pfa = str(self.asciiPart())
        self.fontFile.seek(self.binary[0])
        bin = self.fontFile.read( self.binary[1] )
        pfa = pfa + AsciiHex.asciihex_encode( bin )[0]
        pfa = pfa + '\n' + self.zeroPart()
        return pfa

    def extractPFA( self, chars ):
        pfa = str(self.asciiPart())
        bp = self.binaryPart()
        bin = bp.preambleSection() + bp.subroutinesSection()
        bin += "/CharStrings %d dict dup begin\n" % (len(chars) + 1)
        for cs in self.charStrings():
            if (cs.name in chars) or cs.name == "/.notdef":
                bin += cs.defString()
                bin += "\n"
        bin += bp.tailSection()
        bin = encrypt( bin, eexec_R )
        pfa = pfa + AsciiHex.asciihex_encode( bin )[0]
        pfa = pfa + '\n' + self.zeroPart()
        return pfa

    def partitionPFA(self):
        a = 0
        b = self.findBinarySegment()
        z = self.findZeros()
        self.fontFile.seek(0,2)
        e = self.fontFile.tell()
        self.ascii =  (a,b-a)
        self.binary = (b,z-b)
        self.zeros =  (z, e-z)

    def partitionPFB(self):
        self.fontFile.seek(0)
        h = self.fontFile.read(6)
        a = self.fontFile.tell()
        n = lowEndian( h[2:] )
        self.ascii = (a,n)

        self.fontFile.seek(n,1)
        h = self.fontFile.read(6)
        b = self.fontFile.tell()
        n = lowEndian( h[2:] )
        self.binary = (b,n)

        self.fontFile.seek(n,1)
        h = self.fontFile.read(6)
        z = self.fontFile.tell()
        n = lowEndian( h[2:] )
        self.zeros = (z,n)
        
        self.fontFile.seek(n,1)
        h = self.fontFile.read(2)
        if h[0] != 0x80 or h[1] != 0x03:
            logging.warning("End of file marker missing in pfb file %s (%d %d)",
                            self.fontPath, h[0], h[1])

    def findBinarySegment(self):
        self.fontFile.seek(0)
        pos = 0
        chunk = 1024*4
        backStep = 128
        eexec_re = re.compile(".*currentfile[ ]+eexec[ \n\r\t]",re.DOTALL)

        fbuf = self.fontFile.read( chunk )

        while len(fbuf) > backStep:
            m = eexec_re.match(fbuf) 
            if m:
                binary_start = pos+m.end(0)
                self.fontFile.seek(binary_start)
                return binary_start
                
            self.fontFile.seek( -backStep, 1 )
            pos = self.fontFile.tell()
            fbuf = self.fontFile.read( chunk )
        logging.warning("Unable to find start of binary section in %s", self.fontPath)
        return -1

    def asciiPart( self ):
        if self.aPart == None:
            self.fontFile.seek(self.ascii[0])
            a = self.fontFile.read(self.ascii[1]).decode('latin-1')
            self.aPart = Type1AsciiPart( a )
        return self.aPart

    def binaryPart(self):
        if self.bPart is None:
            self.fontFile.seek(self.binary[0])
            if self.type == PFB_TYPE:
                b = bytearray(self.fontFile.read(self.binary[1]))
            else:
                b = bytearray(AsciiHex.asciihex_decode(
                    self.fontFile.read(self.binary[1]))[0])
            self.bPart = Type1BinaryPart(b)
        return self.bPart

    def zeroPart(self):
        self.fontFile.seek(self.zeros[0])
        return self.fontFile.read(self.zeros[1]).decode('latin-1')

    def findZeros( self ):
        chunk = 1024*4
        self.fontFile.seek(-chunk, 2)
        buf = self.fontFile.read( chunk )
        zcount = 0
        pos = chunk - 1
        while buf:
            c = buf[pos]
            if c == 0x30:  # '0'
                zcount += 1
                if zcount == 512:
                    return self.fontFile.tell()-chunk+pos
            elif not isWhiteSpace[c]:
                zcount = 0
            pos -= 1
            if pos == 0:
                self.fontFile.seek(-chunk, 1)
                buf = self.fontFile.read( chunk )
                pos = chunk - 1

# input b = a string
# does not discard first n bytes of output
# output = a string, some non-printable
#def decrypt(b, R):
#    bytes = array.array('B', b )
#    return decryptBytes( bytes, R).tostring()
eexec_R = 55665
charstring_R = 4330
c1 = 52845
c2 = 22719

def decrypt(s, R):
    if isinstance(s, str):
        s = s.encode('latin-1')
    result = decryptBytes(bytearray(s), R)
    return bytes(result).decode('latin-1')

def decryptBytes( bytes, R):
    try:
        import pscodec
        return pscodec.t1_decrypt( bytes, R )
    except ImportError:
        return decryptBytesSlow( bytes, R )

def decryptBytesSlow(bytes, R):
    mask = (1<<16)-1
    i = 0
    for C in bytes:
        P = C ^ (R >> 8)
        bytes[i] = P
        i = i + 1
        R = ((C + R)*c1 + c2) & mask
    return bytes

def encrypt(s, R):
    if isinstance(s, str):
        s = s.encode('latin-1')
    result = encryptBytes(bytearray(s), R)
    return bytes(result).decode('latin-1')

def encryptBytes( bytes, R):
    try:
        import pscodec
        return pscodec.t1_encrypt( bytes, R )
    except ImportError:
        return encryptBytesSlow( bytes, R )
    
def encryptBytesSlow(bytes, R):
    i = 0
    for P in bytes:
        C = P^(R >> 8)
        bytes[i] = C
        i = i + 1
        R = ((C + R)*c1 + c2) & ((1 << 16)-1)
    return(bytes)

class Type1BinaryPart:

    def __init__(self, binary ):
        result = decryptBytes(bytearray(binary), eexec_R)
        self.bin = bytes(result).decode('latin-1')
        
        rd = self.getRD( )
        self.RD = rd[0]
        self.ND = rd[1]
        self.NP = rd[2]

        self.lenIV = self.getlenIV()

        b = self.bin
        m = re.search("/Subrs[ ]+([0-9]+)[ ]+array[ \t\n\r]*", b)
        self.subrsStart = m.start(0)
        self.subrsCount = int(m.group(1))
        # Theoretically this next line is not safe.  Between /Subrs and /CharStrings
        # there are encrypted strings that could match the following regular expression.
        # This would be a miracle, so we'll do the easy fast thing.
        m = re.search("/CharStrings[ ]+[0-9]+", b)
        self.charStringsStart = m.start(0)
        assert( self.subrsStart < self.charStringsStart )

        self.srArray = None
        self.csDict = None


    def __str__( self ):
        return self.bin

    # We divide the binary part into the following sections, some of which overlap:
    #
    # preambleSection: Everything up to the start of /Subrs
    # subroutinesSection: From /Subrs to the start of /CharStrings
    # interMezzoSection: From the end of the last subroutine definition to the start of /CharStrings
    # charStringsSection: From the start of /CharStrings to the end of the binary part
    # tailSection: From the end of the last CharString definition to the end of the binary part.

    def preambleSection( self ):
        return self.bin[:self.subrsStart]

    def subroutinesSection( self ):
        return self.bin[self.subrsStart:self.charStringsStart]

    def charStringsSection( self ):
        return self.bin[self.charStringsStart:]

    def interMezzoSection( self ):
        b = self.subrsString()
        subr_re =  re.compile("dup[ ]+([0-9]+)[ ]+([0-9]+)[ ]+" + re.escape(self.RD) + " ")

        # Find the last match.
        for m in subr_re.finditer( b ):
            pass
        subr_len = int(m.group(2))
        b = b[m.end(0) + subr_len :]
        
        end_re = re.compile("[ \n\r\t]*%s[ \n\r\t]" % self.ND )
        m = end_re.search( b )
        return b[ m.end(0) : ]

    def tailSection( self ):
        b = self.charStringsSection()
        charString_re =  re.compile("(/[^ \n\t\r]+)[ ]+([0-9]+)[ ]+%s " % re.escape( self.RD ) )
        # Find the last match.
        for m in charString_re.finditer( b ):
            pass
        cs_len = int(m.group(2))
        b = b[m.end(0) + cs_len :]
        
        end_re = re.compile("[ \n\r\t]*%s[ \n\r\t]" % re.escape(self.ND) )
        m = end_re.search( b )
        return b[ m.end(0) : ]

    def getRD( self ):
        """ The examples I have:
        /ND{noaccess def}executeonly def
        /NP{noaccess put}executeonly def
        /RD{string currentfile exch readstring pop}executeonly def
        /|- {noaccess def} executeonly def
        /| {noaccess put} executeonly def
        /-| {string currentfile exch readstring pop} executeonly def """
        b = self.bin
        m = re.search("/([^ / {}]+)[^/]*string[ ]+currentfile", b)
        RD = m.group(1)
        m = re.search("/([^ / {}]+)[^/]*noaccess[ ]+def", b)
        ND = m.group(1)
        m = re.search("/([^ / {}]+)[^/]*noaccess[ ]+put", b)
        NP = m.group(1)
        return( [ RD, ND, NP ] )

    def getlenIV( self ):
        m = re.search("/lenIV[ ]+([0-9]+)[ ]+def", self.bin)
        if m:
            return(int(m.group(1)))
        else:
            return(4)

    def charStrings( self ):
        return CharStringIter( self )

    def subroutines( self ):
        return SubroutineIter( self )

    def subroutine( self, index ):
        v = self._subroutinesArray()
        return CharString( index, v[index], self, decrypted = True )

    def _subroutinesArray( self ):
        if self.srArray != None:
            return self.srArray
        a = [ None ] * self.subrsCount
        for s in self.subroutines():
            # FIXME: What if the index of s exceeds the length of a?
            a[s.name] = s.rawDecryptedString()
        self.srArray = a
        return a

    # FIXME (DM 7/8/2009)
    # The following code for loading charstrings is vastly inefficient.  We should be caching and
    # reading on the fly, rather than loading the whole dict just to read a few characters.
    # The same comments apply to subroutines.  We do the easy thing now to get something
    # working.

    def charStringForGlyph( self, glyphName ):
        d = self._charStringsDict()
        cs = d[glyphName]
        return CharString( glyphName, cs, self, decrypted = True )

    def _charStringsDict( self ):
        if self.csDict != None:
            return self.csDict
        d = {}
        for cs in self.charStrings():
            d[cs.name] = cs.rawDecryptedString()
        self.csDict = d
        return d


class CharString:
    """ Represents either a CharString or a Subroutine in a Type 1 Font.  The data format
    for both is very similar; we make a distinction based on the 'name' field.  If it's a
    Postscript name, then we're a CharString.  If it's an integer, we're a subroutine."""

    def __init__( self, name, csText, binaryPart, decrypted=False ):
        self.name = name    # Either a string (for a charstring) or an integer. If a string, should have the
                                            # leading dash.
        self.csText = csText  # The bytecode text of the character string
        self.binaryPart = binaryPart # Keep ownership of the parent binary part to access field (lenIV, etc.)
        self.decrypted = decrypted # Is the string we've been passed decrypted?

    def encryptedString( self ):
        if( self.decrypted ):
            return encrypt( self.csText, charstring_R )
        return self.csText
        
    def decryptedString( self ):
        """Returns the plaintext string of bytecodes for this charstring, without the leading lenIV bytes"""        
        if( self.decrypted ):
            return self.csText[self.binaryPart.lenIV:]
        return decrypt( self.csText, charstring_R )[self.binaryPart.lenIV:]

    def rawDecryptedString( self ):
        """Returns the plaintext string of bytecodes for this charstring, with the leading lenIV bytes"""        
        if( self.decrypted ):
            return self.csText
        return decrypt( self.csText, charstring_R )

    def subroutine( self, index ):
        return self.binaryPart.subroutine( index )
        
    def defString( self ):
        if isinstance(self.name, str):
            return "%s %d %s %s %s" % (self.name, len(self.csText), self.binaryPart.RD, self.encryptedString(), self.binaryPart.ND )
        return "dup %d %d %s %s %s" % (self.name, len(self.csText), self.binaryPart.RD, self.encryptedString(), self.binaryPart.NP )

    def __str__( self ):
        if isinstance(self.name, str):
            s = "CharString %s: %d bytes" % (self.name, len(self.csText) ) +  "|"
            for c in self.csText:
                s += "<" + str(ord(c)) + ">"
            return s
        return "Subroutine %d: %d bytes" % (self.name, len(self.csText) )

class SubroutineIter:
    def __init__( self, binaryPart ):
        self.text = binaryPart.subroutinesSection()
        self.binaryPart = binaryPart
        subr_re =  re.compile("dup[ ]+([0-9]+)[ ]+([0-9]+)[ ]+" + re.escape(self.binaryPart.RD) + " ")
        self.matchIter = subr_re.finditer( self.text )
        
    def __iter__( self ):
        return self
        
    def __next__(self):
        m = next(self.matchIter)
        if not m:
            raise StopIteration
        csLen = int(m.group(2))
        return CharString(int(m.group(1)),
                          self.text[m.end(0):m.end(0) + csLen],
                          self.binaryPart)

    def next(self):
        return self.__next__()

class CharStringIter:
    def __init__( self, binaryPart ):
        self.binaryPart = binaryPart
        self.text = binaryPart.charStringsSection()
        charString_re =  re.compile("(/[^ \n\r\t]+)[ ]+([0-9]+)[ ]+%s " % re.escape( self.binaryPart.RD ) )
        self.matchIter = charString_re.finditer( self.text )
        
    def __iter__( self ):
        return self
        
    def __next__(self):
        m = next(self.matchIter)
        if not m:
            raise StopIteration
        csLen = int(m.group(2))
        return CharString(m.group(1),
                          self.text[m.end(0):m.end(0) + csLen],
                          self.binaryPart)

    def next(self):
        return self.__next__()
    
class Type1AsciiPart:
    def __init__( self, ascii ):
        self.ascii = ascii
        a = ascii
        encoding_re = re.compile( "/Encoding[ ]+(?:(StandardEncoding)[ \n\r\t]+def|([0-9]+))")
        m = encoding_re.search( a )
        encodingStart = m.start(0)
        self.head = a[:encodingStart]
        if m.groups()[0]:
            # StandardEncoding
            self.tail = a[m.end(0):]
            self.encodingVector = list(StandardEncodingVector)
            return

        numEntries = int(m.groups()[1])
        a = a[encodingStart:]
        entry_re = re.compile( "dup[ ]+([0-9]+)[ ]*(/[^ ]+) put[ \n\r\t]+")
        
        encodingList = [ "/.notDef" ] * numEntries
        startEntries = 0; endEntries = 0
        for m in entry_re.finditer( a ):
            if startEntries == 0:
                startEntries = m.start(0)
            endEntries = m.end(0)
            encodingList[int(m.groups()[0])] = m.groups()[1]
        self.encodingVector = list(encodingList)
        self.tail = a[endEntries:]

    def fontName( self ):
        m = re.search("/FontName[ \t]+/([^ \t]+)",self.ascii)
        return m.groups()[0]

    def fontMatrix( self ):
        fm_re = "/FontMatrix[ \t\n\r]+\[[ \t\n\r]*"
        float_re = "([-+]?(?:\d+(?:\.\d*)?|\.\d+))"
        for k in range(5):
            fm_re +=float_re
            fm_re +="[ \t\n\r]+"
        fm_re +=float_re
        fm_re +="[ \t\n\r]*\]"

        m = re.search(fm_re, self.ascii)
        return [ float(m.group(k+1)) for k in range(6) ]

    def __str__(self):
        return self.ascii
