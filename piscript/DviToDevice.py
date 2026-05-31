from piscript.DviReader import *
from piscript.StringInsert import StringInsert


class DviDevice:
    """Base class for devices that receive DVI rendering commands.

    Subclassed by PysCmdDevice. Each method is a no-op by default;
    subclasses override the ones they need.
    """

    def __init__(self, prefersChars=False):
        pass  # prefersChars was removed — kept for backward compat

    def beginDocument(self, num, den, mag, reader):   pass
    def endDocument(self, reader):                     pass
    def beginPage(self, reader):                       pass
    def endPage(self, reader):                         pass
    def startFont(self, font, scaleFactor, reader):    pass
    def putString(self, string, reader):               pass
    def putRule(self, h, v, a, b):                     pass
    def doSpecial(self, dvc, reader):                  pass


class DviToDevice(DviReader):
    """Intermediary: reads DVI commands and forwards drawing to a DviDevice.

    Batches consecutive characters into StringInsert objects for efficiency.
    """

    def __init__(self, file, device):
        DviReader.__init__(self, file)
        self.device = device
        self.currentString = StringInsert()
        self.lastSentFont = None
        self.lastSentFontSize = 0
        self.origin = None

    # ------------------------------------------------------------------
    #  render
    # ------------------------------------------------------------------

    def render(self):
        self._renderWithStrings()

    def _renderWithStrings(self):
        """Batch consecutive chars into StringInserts for the device."""
        while True:
            c = self.getCommand()
            is_set_char = 0 <= c.index < 132 and not self.currentFont.isVirtual
            if is_set_char:
                if self.currentString.size() == 0:
                    self.h0 = self.h
                    self.v0 = self.v
                self.currentString.addMetric((self.h, self.v))
                c.execute()
                self.adjustbbox(c.getCharIndex())
                self.currentString.addChar(c.getCharIndex())
            else:
                if self.currentString.size() > 0:
                    if self.origin is None:
                        self.origin = [self.h0, self.v0]
                    self.currentString.addMetric((self.h, self.v))
                    self.device.putString(self.currentString, self)
                self.currentString = StringInsert()
                c.execute()
                if 0 <= c.index < 132:
                    self.sendStartFont()
            if c.index == self.EOF():
                self.device.endDocument(self)
                break

    # ------------------------------------------------------------------
    #  font change notification
    # ------------------------------------------------------------------

    def sendStartFont(self):
        if self.currentFont.isVirtual:
            return
        pointSize = self.scaleFactor * self.currentFont.scaledSize
        if (self.currentFont.fontName != self.lastSentFont
                or pointSize != self.lastSentFontSize):
            self.lastSentFont = self.currentFont.fontName
            self.lastSentFontSize = pointSize
            self.device.startFont(self.currentFont, self.scaleFactor, self)

    def _on_font_change(self, dvc, parent_exec):
        """Call parent exec, then notify device of possible font change."""
        parent_exec(self, dvc)
        self.sendStartFont()

    # ------------------------------------------------------------------
    #  exec overrides
    # ------------------------------------------------------------------

    def execPreAmble(self, dvc):
        DviReader.execPreAmble(self, dvc)
        self.device.beginDocument(dvc.num, dvc.den, dvc.mag, self)

    def execBop(self, dvc):
        DviReader.execBop(self, dvc)
        self.device.beginPage(self)

    def execEop(self, dvc):
        DviReader.execEop(self, dvc)
        self.device.endPage(self)

    def execSetRule(self, dvc):
        self.device.putRule(self.h, self.v,
                            dvc.a * self.scaleFactor,
                            dvc.b * self.scaleFactor, self)
        DviReader.execSetRule(self, dvc)

    execPutRule = execSetRule

    def execFntNum(self, dvc):
        self._on_font_change(dvc, DviReader.execFntNum)

    def execFnt(self, dvc):
        self._on_font_change(dvc, DviReader.execFnt)

    def doSpecial(self, dvc):
        self.device.doSpecial(dvc, self)
        DviReader.doSpecial(self, dvc)
