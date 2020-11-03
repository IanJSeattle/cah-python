# vi: set expandtab ai:

import re
from collections import namedtuple
#from typing import List
import game
from player import Player
import cahirc as irc
from chat import CAHmsg


class CmdParser(object):
    """ this class represents the command parsing structure for the
    game. """

    def __init__(self, game):
        # hasargs: command can take arguments
        # required: arguments are required, and a cmd without args will
        # be discarded
        # cardargs: arguments are cards
        # anon: command can be invoked even if not registered in the game
        Attrs = namedtuple('Attrs', 'hasargs required cardargs anon')
        self.cmdattrs = { 
                     'cards': Attrs(False, False, False, False),
                     'commands': Attrs(False, False, False, True),
                     'help': Attrs(False, False, False, True),
                     'join': Attrs(False, False, False, True),
                     'list': Attrs(False, False, False, True),
                     'pick': Attrs(True, True, False, False),
                     'play': Attrs(True, True, True, False),
                     'quit': Attrs(False, False, False, False),
                     'rando': Attrs(True, False, False, True),
                     'reload': Attrs(False, False, False, True),
                     'score': Attrs(False, False, False, False),
                     'shame': Attrs(False, False, False, False),
                     'start': Attrs(True, False, False, True),
                     'state': Attrs(False, False, False, False),
                     'status': Attrs(False, False, False, False),
                     'winner': Attrs(True, True, False, False),
                     }

        # order is important.  aliases will be evaluated in order.
        # 'pick' aliases to 'play' most of the time so that the play()
        # function can deal with out of bound conditions
        Cmdalias = namedtuple('Cmdalias', 'alias command state')
        self.aliases = [ Cmdalias('join', 'start', 'inactive'),
                         Cmdalias('leave', 'quit', 'any'),
                         Cmdalias('pick', 'winner', 'wait_czar'),
                         Cmdalias('pick', 'play', 'any'),
                         Cmdalias('players', 'list', 'any'),
                         Cmdalias('shame', 'score', 'any'),
                         Cmdalias('status', 'state', 'any') ]

        # the maximum number of arguments any command can take
        self.max_args = 3
        self.game = game
        self.ircmsg = None
        self._string = None
        self.player = None
        self.words = []
        self.args = []
        self.command = None

    def is_command(self) -> bool:
        word = self.get_alias()
        if word in self.cmdattrs:
            if not self.cmdattrs[word].hasargs and len(self.words) > 1:
                return False
            return True
        return False

    def get_args(self) -> None:
        for i in range(1, len(self.words)):
            if i > self.max_args:
                return
            if re.search('^\d$', self.words[i]):
                self.args.append(int(self.words[i]))

    def get_commands(self) -> str:
        return ', '.join(sorted(list(self.cmdattrs.keys())))

    def parse(self, msg: CAHmsg=None):
        if msg.message is not None:
            self.string = msg.message
        if not self.is_command():
            self.command = None
            return
        self.command = self.get_alias()
        if self.cmdattrs[self.command]:
            self.player = self.game.get_player(msg.nick)
            registered = True
            if self.player == None:
                self.player = msg.make_player()
                registered = False
            self.get_args()
            if self.args == [] and self.cmdattrs[self.command].required:
                self.command = None
                return
        if self.game.status != 'wait_answers':
            return
        elif registered and self.cmdattrs[self.command].cardargs == True:
            self.play_cards()

    def get_alias(self) -> str:
        for alias in self.aliases:
            if self.words[0] == alias.alias and (self.game.status ==
                alias.state or alias.state == 'any'):
                return alias.command
        return self.words[0]

    def play_cards(self) -> None:
        cardargs = []
        nums = []
        # grab card info from the player's hand
        for arg in self.args:
            nums.append(arg)
            try:
                card = self.player.show_hand()[arg]
            except IndexError:
                pass
            cardargs.append(card)
        # "deal" the cards out to the parser
        self.args = cardargs
        # now remove those cards from player's hand
        for num in nums:
            self.player.deal(num)


    #-----------------------------------------------------------------------
    # properties
    #-----------------------------------------------------------------------

    @property
    def string(self):
        return self._string


    @string.setter
    def string(self, info):
        self._string = info
        self.words = info.split()
