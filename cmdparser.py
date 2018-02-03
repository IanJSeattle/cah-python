# vi: set expandtab ai:

import re
from collections import namedtuple
from typing import List
from game import Game
from player import Player
from cahirc import IRCmsg


class CmdParser(object):
    """ this class represents the command parsing structure for the
    game. """

    def __init__(self, game: Game) -> None:
        # hasargs: command can take arguments
        # required: arguments are required, and a cmd without args will
        # be discarded
        # cardargs: arguments are cards
        # anon: command can be invoked even if not registered in the game
        Attrs = namedtuple('Attrs', 'hasargs required cardargs anon')
        self.cmdattrs = { 'pick': Attrs(True, True, False, False),
                     'play': Attrs(True, True, True, False),
                     'winner': Attrs(True, True, False, False),
                     'start': Attrs(True, False, False, True),
                     'status': Attrs(False, False, False, False),
                     'score': Attrs(False, False, False, False),
                     'shame': Attrs(False, False, False, False),
                     'cards': Attrs(False, False, False, False),
                     'join': Attrs(False, False, False, True)}

        Cmdalias = namedtuple('Cmdalias', 'alias command state')
        self.aliases = [ Cmdalias('pick', 'play', 'wait_answers'),
                         Cmdalias('pick', 'winner', 'wait_czar'),
                         Cmdalias('shame', 'score', 'any') ]

        # the maximum number of arguments any command can take
        self.max_args = 3
        self.game = game
        self.ircmsg = None
        self._string = None
        self.player: Player = None
        self.words: List[str] = []
        self.args: List[int] = []
        self.command: str = None

    def is_command(self) -> bool:
        if self.words[0] in self.cmdattrs:
            return True
        return False

    def get_args(self) -> None:
        for i in range(1, len(self.words)):
            if i > self.max_args:
                return
            if re.search('^\d$', self.words[i]):
                self.args.append(int(self.words[i]))

    def parse(self, msg: IRCmsg=None) -> None:
        if msg.msg is not None:
            self.string = msg.msg
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
        if registered and self.cmdattrs[self.command].cardargs == True:
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
                #import pdb; pdb.set_trace()
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
