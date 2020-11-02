# vi: set expandtab ai wm=1:

import os
import re
import logging
import random
#from typing import List
import config
from deck import Deck
from card import Card
from player import Player
import cmdparser as parser
from random import shuffle
from exceptions import NotPermitted
from util import logtime
import chat

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
        self.rando_player = None
        self.configobj = config.Config()
        self.config = self.configobj.data
        self.lang = self.config['language']
        self.chat = chat.Chat(self)
        self.channel = self.chat.channel

    def __repr__(self):
        return ('Game round: {round}; status: {status}; czar: '
                '{czar}'.format(round=self.round_num, status=self.status,
                czar=self.czar))
    #-----------------------------------------------------------------
    # commands
    #-----------------------------------------------------------------

    def cards(self, player: Player=None, args=None) -> None:
        """ show a player's hand """
        if self.status in ['inactive', 'wait_players']:
            self.chat.say(self.channel, self.get_text('game_not_started'))
            return
        annc = self.get_text('question_announcement')
        annc = annc.format(card=self.question.formattedvalue)
        self.chat.say(player.nick, annc)
        self.show_hand(player)

    def commands(self, player, args):
        self.chat.say(self.channel, parser.CmdParser(self).get_commands())

    def help(self, player, args):
        self.chat.say(self.channel, self.get_text('help_blurb'))

    def join(self, player, args):
        """ add a new player to the game """
        rando = self.config['rando']
        if rando['active'] and player.nick == rando['name']:
            text = self.get_text('no_rando_players')
            text = text.format(rando=rando['name'])
            self.chat.say(self.channel, text)
        elif player in self.players:
            self.chat.say(self.channel, self.get_text('double_join'))
        else:
            self.add_player(player)

    def list(self, player, cards):
        """ list players currently in the game """
        playerlist = [player.nick for player in self.players]
        players = playerlist_format(playerlist)
        annc = self.get_text('player_list')
        annc = annc.format(players=players)
        self.chat.say(self.channel, annc)
 

    @logtime
    def play(self, player, cards):
        """ cards is an array of Card objects """
        if self.status != 'wait_answers':
            # but why did i change all these to be RuntimeError?
            # 20201027-era ian wants to know
            raise RuntimeError
            #return
        if player == self.czar:
            self.chat.say(self.channel, self.get_text('not_player'))
            raise RuntimeError
            #return
        if player not in self.answers:
            if type(cards) is not list:
                cards = [cards]
            else:
                cards = cards
            if len(cards) != self.question.pick:
                error_msg = self.get_text('card_num_wrong')
                answer_word = 'answer'
                if self.question.pick != 1:
                    answer_word = 'answers'
                error_msg = error_msg.format(num=self.question.pick,
                                             answer_word=answer_word,
                                             wrong_num=len(cards))
                self.chat.say(self.channel, error_msg)
                raise RuntimeError
            self.answers[player] = {}
            self.answers[player]['cards'] = cards
            answer = self.format_answer(self.answers[player]['cards'])
            rando = self.config['rando']
            if player.nick != rando['name'] or not rando['active']:
                self.chat.say(player.nick,
                    self.get_text('answer_played').format(answer=answer))
        else:
            self.chat.say(self.channel, self.get_text('already_played'))
            for i in range(self.question.pick):
                player.deck.undeal_last('Answer')
            raise RuntimeError
            #return
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
                self.chat.say(self.channel, text.format(player=player.nick))
        if new_players:
            self.players = new_players
        else:
            self.end_game()
            
    def reload(self, player, args):
        """ reload config files (cards reload with each new game) """
        if self.status != 'inactive':
            self.chat.say(self.channel, self.get_text('reload_wait'))
            return
        self.chat.say(self.channel, self.get_text('reload_announcement'))
        self.configobj.reload()
        self.config = self.configobj.data

    def score(self, player: Player=None, args=None) -> None:
        """ report the current score """
        if self.status == 'inactive':
            return
        scores = self.score_list()
        text = self.get_text('score_announcement')
        text = text.format(scores=scores)
        self.chat.say(self.channel, text)

    def start(self, player: Player=None, args=None) -> None:
        # args are not used in this function
        if self.status != 'inactive':
            self.chat.say(self.channel, self.get_text('game_already_started'))
            return
        self.status = 'wait_players'
        self.chat.say(self.channel, self.get_text('round_start'))
        if player is not None:
            self.add_player(player)
        self.load_cards()
        self.deck.shuffle()
        if self.config['rando']['active']:
            text = self.get_text('rando_enabled')
            text = text.format(rando=self.config['rando']['name'])
            self.chat.say(self.channel, text)
            self.add_rando()
        logger.info('Starting new game')

    def state(self, player, args):
        """ report current game state """
        text = self.get_text('status')
        if self.status == 'inactive':
            self.chat.say(self.channel, text['inactive'])
        elif self.status == 'wait_players':
            msg = text['wait_players']
            msg = msg.format(num=self.config['min_players']-len(self.players))
            self.chat.say(self.channel, msg)
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
            self.chat.say(self.channel, msg)
        elif self.status == 'wait_czar':
            msg = text['wait_czar']
            msg = msg.format(czar=self.czar.nick)
            self.announce_answers(msg)

    @logtime
    def winner(self, player:Player, args):
        """ record the winner of the round """
        if player != self.czar:
            self.chat.say(self.channel, self.get_text('not_czar'))
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
            self.answers = {}
            self.start_round()

    #-----------------------------------------------------------------
    # methods
    #-----------------------------------------------------------------

    def announce_game_winner(self):
        game_winner = self.get_text('game_winner')
        score_element = self.get_text('score_element')
        scores = self.score_list()
        self.chat.say(self.channel, 
                      game_winner.format(player=self.get_game_winner(),
                                         points=self.config['max_points'],
                                         scores=scores))

    # guaranteed not to get a duplicate player
    def add_player(self, player):
        if player not in self.players:
            self.players.append(player)
        players = len(self.players)
        min_players = self.config['min_players']
        game_states = ['wait_answers', 'wait_czar', 'announcing']
        if players >= min_players and self.status == 'wait_players':
            text = self.get_text('welcome_start')
            text = text.format(name=player.nick)
            self.chat.say(self.channel, text)
            self.commence()
        elif players >= min_players and self.status in game_states:
            self.deal_one_player(player, self.config['hand_size'])
            text = self.get_text('welcome_join')
            text = text.format(name=player.nick)
            self.chat.say(self.channel, text)
            self.show_hand(player)
        else:
            text = self.get_text('welcome_wait')
            num = min_players - players
            player_word = 'players' if num > 1 else 'player'
            text = text.format(name=player.nick, num=num, 
                               player_word=player_word)
            self.chat.say(self.channel, text)

    def get_player(self, nick: str) -> Player:
        for player in self.players:
            if player.nick == nick:
                return player
        return None

    def get_text(self, key):
        return self.config['text'][self.lang][key]

    def end_game(self):
        self.status = 'inactive'
        self.round_num = 0
        self.players = []
        self._czar = 0
        self.question = None
        self.answers = {}
        self.answer_order = {}
        self.deck = Deck()
        self.chat.say(self.channel, self.get_text('game_start'))

    def next_czar(self) -> None:
        self._czar += 1
        self._czar %= len(self.players)
        if self.czar.nick == self.config['rando']['name']:
            return self.next_czar()
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
        self.chat.say(self.channel, round_annc)
        self.chat.say(self.channel, card_annc.format(card=q_text))
        self.show_hands()
        if self.config['rando']['active']:
            if self.czar.nick == self.config['rando']['name']:
                self.next_czar()
            self.play_rando()

    @logtime
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
        msg = '{player} called {cmd} command'.format(player=parser.player,
                                                     cmd=parser.command)
        logger.info(msg)
        func = getattr(self, parser.command)
        try:
            func(parser.player, parser.args)
        except RuntimeError:
            pass

    def deal_one_player(self, player, num):
        for i in range(num):
            card = self.deck.deal('Answer')
            player.add_card(card)
        cards = len(player.deck)

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
        self.chat.say(self.channel, text)

    def announce_answers(self, text):
        self.chat.say(self.channel, text)
        players = self.randomize_answers()
        for i, player in enumerate(players):
            cards = self.answers[player]['cards']
            self.chat.say(self.channel, 
                          '[{}] {}'.format(i, self.format_answer(cards)))
        self.chat.say(self.channel, 
                      self.get_text('czar_pick').format(czar=self.czar.nick))
 
    def format_answer(self, cards):
        spaces = self.question.value.count('%s')
        remain_space = len(cards) - spaces
        text = re.sub('%s', '{}', self.question.value)
        if isinstance(cards[0], Card):
            answers = [card.value for card in cards]
        else:
            answers = cards
        if remain_space:
            text += ' ' + ' '.join(['{}' for i in range(remain_space)])
        text = text.format(*answers)
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
        rando = self.config['rando']
        if player == self.czar or (rando['active'] and player.nick ==\
            rando['name']):
            return
        hand = player.show_hand()
        annc = self.get_text('player_hand')
        handstring = ' '.join(['[{}] {}'.format(i, card) 
            for i, card
            in enumerate(hand)])
        self.chat.say(player.nick, annc.format(cards=handstring))

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
                return player.nick
        return None

    def play_rando(self):
        rando = None
        for player in self.players:
            if player.nick == self.config['rando']['name']:
                rando = player
                break
        cards = [rando.deal(random.randint(0, len(rando.deck)-1))
                 for i in range(self.question.pick)]
        self.play(rando, cards)
        text = self.get_text('rando_played')
        text = text.format(rando=self.config['rando']['name'])
        self.chat.say(self.channel, text)

    def add_rando(self):
            rando = Player(self.config['rando']['name'])
            self.players.append(rando)
            self.deal_one_player(rando, self.config['hand_size'])
            #self._czar += 1
        

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
    playerlist = sorted(playerlist)
    size = len(playerlist)
    if size == 1:
        return playerlist[0]
    if size == 2:
        return ' and '.join(playerlist)
    if size > 2:
        return ', '.join(playerlist[0:-1]) + ' and ' + playerlist[-1]
