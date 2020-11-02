# vi: set et ai sm:

import re

class Card(object):
    def __init__(self, cardtype, value):
        self.cardtype = cardtype # either 'Question' or 'Answer'
        self.value = value
        self.draw = 0
        self.pick = 1
        self.source = 'unknown'

    def __repr__(self):
        return self.info()

    def info(self):
        return '[{}] {}: {} (pick {} draw {})'.format(self.source,
            self.cardtype, self.value, self.pick, self.draw)

    @property
    def formattedvalue(self):
        return re.sub('%s', '___', self.value)
