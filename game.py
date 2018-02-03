# vi: set expandtab ai:

import config, os, re
from typing import List
from deck import Deck
from card import Card
from player import Player
from cahirc import Cahirc
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
        self.answer_order = {}
        self.deck = Deck()
        self.config = config.Config().data
        self.lang = self.config['language']
        self.channel = self.config['default_channel']
        self.irc = Cahirc(self)
        
    #-----------------------------------------------------------------
    # commands
    #-----------------------------------------------------------------

    def start(self, player:Player=None, args:List=None):
        # args are not used in this function
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

    def winner(self, player:Player, answer_num):
        """ record the winner of the round """
        # player is the player who made the call; ignore
        person = self.answer_order[answer_num]
        person.record_win()
        self.announce_winner(person)
        self.next_czar()

    def join(self, player, args):
        """ add a new player to the game """
        if player in self.players:
            self.irc.say(self.channel, 
                self.config['text'][self.lang]['double_join'])
        else:
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

    def get_player(self, nick: str) -> Player:
        for player in self.players:
            if player.nick == nick:
                return player
        return None

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
            czar=self.czar.nick)
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
        if parser.command is None:
            return
        func = getattr(self, parser.command)
        func(parser.player, parser.args)

    def deal_all_players(self, num):
        for i in range(num):
            for player in self.players:
                card = self.deck.deal('Answer')
                player.add_card(card)

    def announce_winner(self, player:Player) -> None:
        lang = self.config['language']
        text = self.config['text'][lang]['winner_announcement']
        text = text.format(player=player.nick, 
            card=self.format_answer(self.answers[player]['cards']),
            points=player.points)
        self.irc.say(self.channel, text)

    def announce_answers(self):
        annc = self.config['text'][self.lang]['all_cards_played']
        self.irc.say(self.channel, annc)
        players = self.randomize_answers()
        for player in players:
            cards = self.answers[player]['cards']
            self.irc.say(self.channel, self.format_answer(cards))
            
    def format_answer(self, cards):
        # TODO: add extra {}s on the end to add up to the PICK number
        text = re.sub('%s', '{}', self.question.value)
        answers = [card.value for card in cards]
        try:
            text = text.format(*answers)
        except IndexError as err:
            print('incorrect number of cards supplied')
            print('cards: {}'.format(cards))
            print('question: {}'.format(self.question.value))
        return text

    def randomize_answers(self):
        players = list(self.answers.keys())
        shuffle(players)
        i = 0
        for player in players:
            self.answer_order[i] = player
            self.answers[player]['order'] = i
            i += 1
        return players

    def receive_irc(self, source, nick, user, msg):
        ''' receive some IRC goodness here'''

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
            self.irc.say(player.nick, annc.format(cards=handstring))


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
