# vi: set expandtab ai:

import config
from deck import Deck
from card import Card
from player import Player

class Game(object):
    def __init__(self):
        self.status_codes = ['inactive', 'wait_players', 'wait_answers', 
            'wait_czar']
        self._status = 'invalid'
        self.status = 'inactive'
        self.players = []
        self.czar = 0
        self.answers = {}
        self.deck = Deck()
        self.channel = config.CONFIG['default_channel']
        
    def start(self):
        self.status = 'wait_players'
        # TODO: announce the start of the game

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, state):
        if state in self.status_codes:
            self._status = state
        else:
            raise ValueError('No such game state')
