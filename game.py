# vi: set expandtab ai:

import config
import os
import re
#from typing import List
from deck import Deck
from card import Card
from player import Player
import cahirc as irc
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
        self.irc = irc.Cahirc(self)

    #-----------------------------------------------------------------
    # commands
    #-----------------------------------------------------------------

    def cards(self, player: Player=None, args: List=None) -> None:
        """ show a player's hand """
        self.irc.destination = player.nick
        if self.status in ['inactive', 'wait_players']:
            self.irc.say(self.config['text'][self.lang]['game_not_started'])
            return
        annc = self.config['text'][self.lang]['question_announcement']
        annc = annc.format(card=self.question.formattedvalue)
        self.irc.say(annc)
        self.show_hand(player)

    def join(self, player, args):
        """ add a new player to the game """
        if player in self.players:
            self.irc.say(self.config['text'][self.lang]['double_join'])
        else:
            self.add_player(player)

    def list(self, player, cards):
        """ list players currently in the game """
        playerlist = [player.nick for player in self.players]
        players = playerlist_format(playerlist)
        annc = self.config['text']['en']['player_list']
        annc = annc.format(players=players)
        self.irc.say(annc)
 

    def play(self, player, cards):
        """ cards is an array of Card objects """
        if self.status != 'wait_answers':
            return
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

    def score(self, player: Player=None, args: List=None) -> None:
        """ report the current score """
        self.irc.say('This feature is not yet implemented')

    def start(self, player: Player=None, args: List=None) -> None:
        # args are not used in this function
        self.status = 'wait_players'
        if player is not None:
            self.add_player(player)
        self.load_cards()
        self.deck.shuffle()
        text = self.config['text'][self.lang]['round_start']
        self.irc.say(text)

    def state(self, player, args):
        """ report current game state """
        if self.status == 'inactive':
            self.irc.say(self.config['text'][self.lang]['status']['inactive'])
        elif self.status == 'wait_players':
            msg = self.config['text'][self.lang]['status']['wait_players']
            msg = msg.format(num=self.config['min_players']-len(self.players))
            self.irc.say(msg)
        elif self.status == 'wait_answers':
            all_players = set([player.nick for player in self.players]) 
            played = set([player.nick for player in self.answers])
            czar = set([self.czar.nick])
            playerlist = all_players - played
            playerlist = playerlist - czar
            players = playerlist_format(list(playerlist))
            question = self.question.formattedvalue
            msg = self.config['text'][self.lang]['status']['wait_answers']
            msg = msg.format(players=players, question=question)
            self.irc.say(msg)

    def winner(self, player:Player, args):
        """ record the winner of the round """
        # player is the player who made the call; ignore
        answer_num = args[0]
        person = self.answer_order[answer_num]
        person.record_win()
        self.announce_winner(person)
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

    def get_player(self, nick: str) -> Player:
        for player in self.players:
            if player.nick == nick:
                return player
        return None

    def next_czar(self) -> int:
        self._czar += 1
        self._czar %= len(self.players)
        return self.czar

    def commence(self) -> None:
        self.deal_all_players(self.config['hand_size'])
        self.start_round()

    def start_round(self):
        self.round_num += 1
        self.status = 'wait_answers'
        self.question = self.deck.deal('Question')
        q_text = self.question.formattedvalue
        round_annc = self.config['text'][self.lang]['round_announcement']
        round_annc = round_annc.format(round_num=self.round_num,
            czar=self.czar.nick)
        card_annc = self.config['text'][self.lang]['question_announcement']
        self.irc.say(round_annc)
        self.irc.say(card_annc.format(card=q_text))
        self.show_hands()

    def load_cards(self):
        self.deck = Deck()
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
        #import pdb; pdb.set_trace()
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
        self.irc.say(text)

    def announce_answers(self):
        annc = self.config['text'][self.lang]['all_cards_played']
        self.irc.say(annc)
        players = self.randomize_answers()
        for player in players:
            cards = self.answers[player]['cards']
            self.irc.say(self.format_answer(cards))
 
    def format_answer(self, cards):
        # TODO: add extra {}s on the end to add up to the PICK number
        text = re.sub('%s', '{}', self.question.value)
        if isinstance(cards[0], Card):
            answers = [card.value for card in cards]
        else:
            answers = cards
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

    def show_hands(self):
        for player in self.players:
            self.show_hand(player)

    def show_hand(self, player):
        if player == self.czar:
            return
        hand = player.show_hand()
        annc = self.config['text'][self.lang]['player_hand']
        handstring = ''
        i = 0
        for card in hand:
            handstring += '[{}] {} '.format(i, card)
            i += 1
        self.irc.destination = player.nick
        self.irc.say(annc.format(cards=handstring))


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


def playerlist_format(playerlist):
    size = len(playerlist)
    if size == 1:
        return playerlist[0]
    if size == 2:
        return ' and '.join(playerlist)
    if size > 2:
        return ', '.join(playerlist[0:-1]) + ' and ' + playerlist[-1]
