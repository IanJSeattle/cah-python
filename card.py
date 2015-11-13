class Card(object):
    def __init__(self, cardtype, value):
        self.cardtype = cardtype
        self.value = value
        self.draw = 0
        self.pick = 1
        self.source = 'unknown'

    def info(self):
        return '[{}] {}: {} (pick {} draw {})'.format(self.source,
            self.cardtype, self.value, self.pick, self.draw)
