from dataclasses import dataclass, field


@dataclass
class StringInsert:
    string: list = field(default_factory=list)
    metrics: list = field(default_factory=list)

    def size(self):
        return len(self.string)

    def addChar(self, i):
        self.string.append(i)

    def addMetric(self, m):
        self.metrics.append(m)
