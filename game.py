# vi: set expandtab ai:

from deck import Deck
from card import Card
from player import Player

class Game(object):
    def __init__(self):
        self.in_progress = False
        self.players = []
        self.answers = {}
        self.deck = Deck()
        self.channel = config.CONFIG['default_channel']
