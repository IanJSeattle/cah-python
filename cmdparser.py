# vi: set expandtab ai:

import re
from collections import namedtuple


class CmdParser(object):
    """ this class represents the command parsing structure for the
    game. """

    def __init__(self, string, game):
        self.Args = namedtuple('Args', 'hasargs required')
        self.cmdargs = { 'pick': self.Args(hasargs=True, required=True),
                     'play': self.Args(hasargs=True, required=True),
                     'winner': self.Args(hasargs=True, required=True),
                     'start': self.Args(hasargs=True, required=False),
                     'status': self.Args(hasargs=False, required=False),
                     'score': self.Args(hasargs=False, required=False),
                     'shame': self.Args(hasargs=False, required=False),
                     'cards': self.Args(hasargs=False, required=False),
                     'join': self.Args(hasargs=False, required=False)}

        self.Cmdalias = namedtuple('Cmdalias', 'alias command state')
        self.aliases = [ self.Cmdalias('pick', 'play', 'wait_answers'),
                         self.Cmdalias('pick', 'winner', 'wait_czar'),
                         self.Cmdalias('shame', 'score', 'any') ]

        # the maximum number of arguments any command can take
        self.max_args = 3
        self.game = game
        self.string = string
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

    def parse(self):
        if not self.is_command():
            self.command = None
            return
        self.command = self.get_alias()
        if self.cmdargs[self.command]:
            self.get_args()
            if self.args == [] and self.cmdargs[self.command].required:
                self.command = None

    def get_alias(self):
        for alias in self.aliases:
            if self.words[0] == alias.alias and self.game.status == alias.state:
                return alias.command
        return self.words[0]
