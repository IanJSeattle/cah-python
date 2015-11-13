class Player(object):
    def __init__(self, name):
        self.name = name
        self.deck = None
        self.game_wins = 0
        self.overall_wins = 0
        self.games_played = 0

    def record_win(self):
        self.game_wins += 1

    def game_win(self):
        self.overall_wins += 1
        self.games_played += 1

    def get_score(self):
        return (self.game_wins, self.overall_wins, self.games_played)
