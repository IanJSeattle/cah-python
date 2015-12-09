# vi: set expandtab ai:

import re
from collections import namedtuple


class CmdParser(object):
    """ this class represents the command parsing structure for the
    game. """

    def __init__(self, string, game, player=None):
        self.Args = namedtuple('Args', 'hasargs required cardargs')
        self.cmdargs = { 'pick': self.Args(True, True, False),
                     'play': self.Args(True, True, True),
                     'winner': self.Args(True, True, False),
                     'start': self.Args(True, False, False),
                     'status': self.Args(False, False, False),
                     'score': self.Args(False, False, False),
                     'shame': self.Args(False, False, False),
                     'cards': self.Args(False, False, False),
                     'join': self.Args(False, False, False)}

        self.Cmdalias = namedtuple('Cmdalias', 'alias command state')
        self.aliases = [ self.Cmdalias('pick', 'play', 'wait_answers'),
                         self.Cmdalias('pick', 'winner', 'wait_czar'),
                         self.Cmdalias('shame', 'score', 'any') ]

        # the maximum number of arguments any command can take
        self.max_args = 3
        self.game = game
        self.string = string
        self.player = player
        self.words = string.split()
        self.args = []
        self.command = None
        self.parse()

    def is_command(self):
        if self.words[0] in self.cmdargs:
            return True
        return False

    def get_args(self):
        for i in range(1, len(self.words)):
            if i > self.max_args:
                return
            if re.search('^\d$', self.words[i]):
                self.args.append(int(self.words[i]))

    def parse(self, string=None):
        if string is not None:
            self.string = string
        if not self.is_command():
            self.command = None
            return
        self.command = self.get_alias()
        if self.cmdargs[self.command]:
            self.get_args()
            if self.args == [] and self.cmdargs[self.command].required:
                self.command = None
        if self.player is not None and self.cmdargs[self.command].cardargs == True:
            self.deal_cards()

    def get_alias(self):
        for alias in self.aliases:
            if self.words[0] == alias.alias and (self.game.status == 
                alias.state or alias.state == 'any'):
                return alias.command
        return self.words[0]

    def deal_cards(self):
        cardargs = []
        nums = []
        # this seemed easier than doing math to track cards as they're
        # dealt
        for arg in self.args:
            nums.append(arg)
            card = self.player.show_hand()[arg]
            cardargs.append(card)
        self.args = cardargs
        # now discard those cards from player's hand
        for num in nums:
            self.player.deal(num)
