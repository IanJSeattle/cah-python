# vi: set expandtab ai wm=1:

import os
import re
import logging
#from typing import List
import config
from deck import Deck
from card import Card
from player import Player
import cmdparser as parser
import cahirc as irc
from random import shuffle
from exceptions import NotPermitted

logger = logging.getLogger(__name__)

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
        self.irc.start()
        self.irc.say(self.get_text('game_start'))

    #-----------------------------------------------------------------
    # commands
    #-----------------------------------------------------------------

    def cards(self, player: Player=None, args=None) -> None:
        """ show a player's hand """
        self.irc.destination = player.nick
        if self.status in ['inactive', 'wait_players']:
            self.irc.say(self.get_text('game_not_started'))
            return
        annc = self.get_text('question_announcement')
        annc = annc.format(card=self.question.formattedvalue)
        self.irc.say(annc)
        self.show_hand(player)

    def commands(self, player, args):
        self.irc.say(parser.CmdParser(self).get_commands())

    def help(self, player, args):
        self.irc.say(self.get_text('help_blurb'))

    def join(self, player, args):
        """ add a new player to the game """
        if player in self.players:
            self.irc.say(self.get_text('double_join'))
        else:
            self.add_player(player)

    def list(self, player, cards):
        """ list players currently in the game """
        playerlist = [player.nick for player in self.players]
        players = playerlist_format(playerlist)
        annc = self.get_text('player_list')
        annc = annc.format(players=players)
        self.irc.say(annc)
 

    def play(self, player, cards):
        """ cards is an array of Card objects """
        if self.status != 'wait_answers':
            return
        if player == self.czar:
            self.irc.say(self.get_text('not_player'))
            return
        if player not in self.answers:
            self.answers[player] = {}
            if type(cards) is not list:
                self.answers[player]['cards'] = [cards]
            else:
                self.answers[player]['cards'] = cards
        else:
            self.irc.say(self.get_text('already_played'))
            for i in range(self.question.pick):
                player.deck.undeal_last('Answer')
            return
        if len(self.answers) == len(self.players) - 1:
            self.status = 'wait_czar'
            annc = self.get_text('all_cards_played')
            self.announce_answers(annc)

    def quit(self, player: Player=None, args=None) -> None:
        """ remove player from the game """
        text = self.get_text('quit_message')
        new_players = []
        for pl in self.players:
            if pl != player:
                new_players.append(pl)
            else:
                self.irc.say(text.format(player=player.nick))
        if new_players:
            self.players = new_players
        else:
            self.end_game()
            
    def score(self, player: Player=None, args=None) -> None:
        """ report the current score """
        if self.status == 'inactive':
            return
        scores = self.score_list()
        text = self.get_text('score_announcement')
        text = text.format(scores=scores)
        self.irc.say(text)

    def start(self, player: Player=None, args=None) -> None:
        # args are not used in this function
        if self.status != 'inactive':
            self.irc.say(self.get_text('game_already_started'))
            return
        self.status = 'wait_players'
        self.irc.say(self.get_text('round_start'))
        if player is not None:
            self.add_player(player)
        self.load_cards()
        self.deck.shuffle()

    def state(self, player, args):
        """ report current game state """
        text = self.get_text('status')
        if self.status == 'inactive':
            self.irc.say(text['inactive'])
        elif self.status == 'wait_players':
            msg = text['wait_players']
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
            msg = text['wait_answers']
            msg = msg.format(players=players, question=question)
            self.irc.say(msg)
        elif self.status == 'wait_czar':
            msg = text['wait_czar']
            msg = msg.format(czar=self.czar.nick)
            self.announce_answers(msg)

    def winner(self, player:Player, args):
        """ record the winner of the round """
        if player != self.czar:
            self.irc.say(self.get_text('not_czar'))
            return
        answer_num = args[0]
        person = self.answer_order[answer_num]
        person.record_win()
        self.announce_winner(person)
        self.next_czar()
        self.top_up_hands()
        game_winner = self.get_game_winner()
        if game_winner:
            self.announce_game_winner()
            self.end_game()
        else:
            self.start_round()

    #-----------------------------------------------------------------
    # methods
    #-----------------------------------------------------------------

    def announce_game_winner(self):
        game_winner = self.get_text('game_winner')
        score_element = self.get_text('score_element')
        scores = self.score_list()
        self.irc.say(game_winner.format(player=self.get_game_winner(),
                                        points=self.config['max_points'],
                                        scores=scores))

    # guaranteed not to get a duplicate player
    def add_player(self, player):
        if player not in self.players:
            self.players.append(player)
        players = len(self.players)
        min_players = self.config['min_players']
        if players >= min_players and self.status == 'wait_players':
            text = self.get_text('welcome_start')
            text = text.format(name=player.nick)
            self.irc.say(text)
            self.commence()
        else:
            text = self.get_text('welcome_wait')
            num = min_players - players
            player_word = 'players' if num > 1 else 'player'
            text = text.format(name=player.nick, num=num, 
                               player_word=player_word)
            self.irc.say(text)

    def get_player(self, nick: str) -> Player:
        for player in self.players:
            if player.nick == nick:
                return player
        return None

    def get_text(self, key):
        return self.config['text'][self.lang][key]

    def end_game(self):
        self.__init__()

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
        round_annc = self.get_text('round_announcement')
        round_annc = round_annc.format(round_num=self.round_num,
            czar=self.czar.nick)
        card_annc = self.get_text('question_announcement')
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
        logger.info('{player} called {cmd} command'.format(player=parser.player,
                                                           cmd=parser.command))
        func = getattr(self, parser.command)
        func(parser.player, parser.args)

    def deal_all_players(self, num):
        for i in range(num):
            for player in self.players:
                card = self.deck.deal('Answer')
                player.add_card(card)

    def top_up_hands(self):
        for player in self.players:
            missing = self.config['hand_size'] - len(player.deck)
            if missing:
                for i in range(missing):
                    card = self.deck.deal('Answer')
                    player.add_card(card)

    def announce_winner(self, player:Player) -> None:
        text = self.get_text('winner_announcement')
        text = text.format(player=player.nick,
            card=self.format_answer(self.answers[player]['cards']),
            points=player.points)
        self.irc.say(text)

    def announce_answers(self, text):
        self.irc.say(text)
        players = self.randomize_answers()
        for i, player in enumerate(players):
            cards = self.answers[player]['cards']
            self.irc.say('[{}] {}'.format(i, self.format_answer(cards)))
 
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
            # TODO: replace this with logging calls
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
        annc = self.get_text('player_hand')
        handstring = ''
        i = 0
        for card in hand:
            handstring += '[{}] {} '.format(i, card)
            i += 1
        self.irc.destination = player.nick
        self.irc.say(annc.format(cards=handstring))

    def score_list(self):
        max_points = self.config['max_points']
        text = self.get_text('score_element')
        def point_word(points):
            return 'point' if points == 1 else 'points'
        score_order = [text.format(player=pl.nick, points=pl.points,
                       point_word=point_word(pl.points)) for pl in 
                       sorted(self.players, key=lambda p: max_points -
                       p.points)]
        return ', '.join(score_order)

    def get_game_winner(self):
        max_points = self.config['max_points']
        for player in self.players:
            if player.get_score()[0] == max_points:
                return player
        return None


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
