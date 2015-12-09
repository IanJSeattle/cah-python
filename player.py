# vi: set expandtab ai:

from deck import Deck

class Player(object):
    def __init__(self, ID):
        self.ID = ID
        self.name = ID
        self.deck = Deck()
        self.game_wins = 0
        self.overall_wins = 0
        self.games_played = 0

    def __repr__(self):
        return '{} [{}, {}/{}]'.format(self.name, self.game_wins,
            self.overall_wins, self.games_played)

    def record_win(self):
        self.game_wins += 1

    def game_win(self):
        self.game_wins = 0
        self.overall_wins += 1
        self.games_played += 1

    def get_score(self):
        return (self.game_wins, self.overall_wins, self.games_played)
    
    def show_hand(self):
        return self.deck.show_hand('Answer')

    def add_card(self, card):
        self.deck.add(card)

    def deal(self, num):
        return self.deck.deal('Answer', num)
