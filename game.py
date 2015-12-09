# vi: set expandtab ai:

import config, os
from deck import Deck
from card import Card
from player import Player
from cahirc import IRCBot
import cahirc

class Game(object):
    def __init__(self):
        self.status_codes = ['inactive', 'wait_players', 'wait_answers', 
            'wait_czar', 'announcing']
        self._status = 'invalid'
        self.status = 'inactive'
        self.players = []
        self._czar = 0
        self.question = None
        self.answers = {}
        self.deck = Deck()
        self.config = config.Config().data
        self.channel = self.config['default_channel']
        self.irc = cahirc.IRCBot(self.config['default_channel'],
            self.config['my_nick'], self.config['server'])
        
    #-----------------------------------------------------------------
    # commands
    #-----------------------------------------------------------------

    def start(self, player=None, throwaway=None):
        self.status = 'wait_players'
        if player is not None:
            self.add_player(player)
        self.load_cards()
        self.deck.shuffle()
        text = self.config['text']['en']['round_start']
        self.irc.say(self.channel, text)
        # TODO: announce the start of the game

    def play(self, player, cards):
        """ cards is an array of Card objects """
        if player == self.czar:
            raise RuntimeError('czar may not play')
        if player not in self.answers:
            self.answers[player] = cards
        else:
            raise RuntimeError('multiple answers not allowed')
        if len(self.answers) == len(self.players) - 1:
            self.status = 'wait_czar'
            self.announce()

    def winner(self, player):
        """ record the winner of the round """
        player.game_wins += 1
        self.next_czar()


    #-----------------------------------------------------------------
    # methods
    #-----------------------------------------------------------------

    def add_player(self, player):
        if player not in self.players:
            self.players.append(player)
        players = len(self.players)
        min_players = self.config['min_players']
        if players >= min_players and self.status == 'wait_players':
            self.commence()

    def next_czar(self):
        self._czar += 1
        if self._czar >= len(self.players):
            self._czar = 0
        return self.czar

    def commence(self):
        self.status = 'wait_answers'
        self.question = self.deck.deal('Question')
        self.deal_all_players(10)
        # TODO: announce question

    def load_cards(self):
        currdir = os.getcwd()
        os.chdir(self.config['carddir'])
        files = os.listdir()
        for thisfile in files:
            if thisfile.endswith('json'):
                self.deck.read_in(thisfile)
        os.chdir(currdir)

    def command(self, parser):
        func = getattr(self, parser.command)
        func(parser.player, parser.args)

    def deal_all_players(self, num):
        for i in range(10):
            for player in self.players:
                card = self.deck.deal('Answer')
                player.add_card(card)

    def announce(self):
        pass


    #-----------------------------------------------------------------
    # getters and setters
    #-----------------------------------------------------------------

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, state):
        if state in self.status_codes:
            self._status = state
        else:
            raise ValueError('No such game state')
    
    @property
    def czar(self):
        return self.players[self._czar]
