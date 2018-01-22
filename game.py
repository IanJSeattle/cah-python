# vi: set expandtab ai:

import config, os, re
from deck import Deck
from card import Card
from player import Player
from cahirc import IRCBot
import cahirc
from random import shuffle
from exceptions import NotPermitted

class Game(object):
    def __init__(self):
        self.status_codes = ['inactive', 'wait_players', 'wait_answers', 
            'wait_czar', 'announcing']
        self._status = 'invalid'
        self.status = 'inactive'
        self.round_num = 0
        self.players = []
        self._czar = 0
        self.question = None
        self.answers = {}
        self.deck = Deck()
        self.config = config.Config().data
        self.lang = self.config['language']
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
        text = self.config['text'][self.lang]['round_start']
        self.irc.say(self.channel, text)
        # TODO: announce the start of the game

    def play(self, player, cards):
        """ cards is an array of Card objects """
        if player == self.czar:
            raise NotPermitted('czar may not play')
        if player not in self.answers:
            self.answers[player] = {}
            if type(cards) is not list:
                self.answers[player]['cards'] = [cards]
            else:
                self.answers[player]['cards'] = cards
        else:
            raise NotPermitted('multiple answers not allowed')
        if len(self.answers) == len(self.players) - 1:
            self.status = 'wait_czar'
            self.announce_answers()

    def winner(self, player):
        """ record the winner of the round """
        player.record_win()
        self.next_czar()

    def join(self, player, args):
        """ add a new player to the game """
        self.add_player(player)


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
        self._czar %= len(self.players)
        return self.czar

    def commence(self):
        self.deal_all_players(self.config['hand_size'])
        self.start_round()

    def start_round(self):
        self.round_num += 1
        self.status = 'wait_answers'
        self.question = self.deck.deal('Question')
        q_text = re.sub('%s', '___', self.question.value)
        round_annc = self.config['text'][self.lang]['round_announcement']
        round_annc = round_annc.format(round_num=self.round_num, 
            czar=self.czar.name)
        card_annc = self.config['text'][self.lang]['question_announcement']
        self.irc.say(self.channel, round_annc)
        self.irc.say(self.channel, card_annc.format(card=q_text))
        self.show_hands()

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
        for i in range(num):
            for player in self.players:
                card = self.deck.deal('Answer')
                player.add_card(card)

    def announce_answers(self):
        annc = self.config['text'][self.lang]['all_cards_played']
        self.irc.say(self.channel, annc)
        # TODO: randomize answer order
        players = self.randomize_answers()
        for player in players:
            cards = self.answers[player]['cards']
            self.irc.say(self.channel, self.format_answer(cards))
            
    def format_answer(self, cards):
        # TODO: add extra {}s on the end to add up to the PICK number
        text = re.sub('%s', '{}', self.question.value)
        answers = [card.value for card in cards]
        try:
            text.format(*answers)
        except IndexError as err:
            print('cards: {}'.format(cards))
            print('question: {}'.format(self.question.value))
        return text

    def randomize_answers(self):
        players = list(self.answers.keys())
        shuffle(players)
        i = 0
        for player in players:
            self.answers[player]['order'] = i
            i += 1
        return players

    def show_hands(self):
        for player in self.players:
            if player == self.czar:
                continue
            hand = player.show_hand()
            annc = self.config['text'][self.lang]['player_hand']
            handstring = ''
            i = 0
            for card in hand:
                handstring += '[{}] {} '.format(i, card)
                i += 1
            self.irc.say(player.name, annc.format(cards=handstring))


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
