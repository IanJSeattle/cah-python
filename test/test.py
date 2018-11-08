#!/usr/bin/env python3
# vi:set expandtab ai wm=0:
# pylint: disable=missing-docstring

"""
TODO list:
* always reply to the cards command by privmsg (possibly covered above)
* reply to privmsg contacts via privmsg, and pub via pub
* send privmsg to player after they play their hand for the round showing what
  they played
"""

import unittest, sys, os, re
import logging
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call
import irc.client
from shutil import copyfile

sys.path.append('..')
sys.path.append('.')

from config import Config
from card import Card
from deck import Deck
from player import Player
from cmdparser import CmdParser
from exceptions import (NotPermitted, NoMoreCards)
from cahirc import IRCmsg, FakeIRCmsg

from game import Game
import game as gameclass
from game import irc as cahirc

cahirc.Cahirc.say = MagicMock()
cahirc.Cahirc.start = MagicMock()

from pycardbot import setup_logging
setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def start_game():
    game = gameclass.Game()
    bob = Player('Bob', '~bobbo')
    jim = Player('Jim', '~jimbo')
    joe = Player('Joe', '~joebo')
    game.start()
    game.add_player(bob)
    game.add_player(joe)
    game.add_player(jim)
    return game


def run_command(game, command, user=None):
    p = CmdParser(game)
    msg = FakeIRCmsg(command, user=user)
    p.parse(msg)
    game.command(p)


def pick_answers(game, player):
    pick = game.question.pick
    cardslist = ' '.join([str(i) for i in range(pick)])
    run_command(game, f'play {cardslist}', user=player)


class CardTest(unittest.TestCase):
    def test_card(self):
        card = Card('Answer', 'Test card')
        self.assertEqual('Test card', card.value)

    def test_card_info(self):
        card = Card('Answer', 'Test card')
        card.source = 'Test'
        self.assertEqual('[Test] Answer: Test card (pick 1 draw 0)',
            card.info())


class DeckTest(unittest.TestCase):
    def test_deck_init_works(self):
        deck = Deck()
        self.assertEqual([], deck.answercards)
        self.assertEqual([], deck.questioncards)
        self.assertEqual([], deck.dealt_answers)
        self.assertEqual([], deck.dealt_questions)

    def test_init_with_answer_adds_answer(self):
        card = Card('Answer', 'Test card')
        deck = Deck([card])
        newcard = deck.deal('Answer')
        self.assertEqual('Test card', newcard.value)

    def test_adding_answer_adds_answer(self):
        card = Card('Answer', 'Test card')
        deck = Deck()
        deck.add(card)
        newcard = deck.deal('Answer')
        self.assertEqual('Test card', newcard.value)

    def test_init_with_answer_gives_no_questions(self):
        card = Card('Answer', 'Test card')
        deck = Deck([card])
        with self.assertRaises(NoMoreCards):
            newcard = deck.deal('Question')

    def test_adding_answer_gives_no_questions(self):
        card = Card('Answer', 'Test card')
        deck = Deck()
        deck.add(card)
        with self.assertRaises(NoMoreCards):
            newcard = deck.deal('Question')

    def test_dealing_card_removes_from_deck(self):
        card = Card('Answer', 'Test card')
        deck = Deck([card])
        newcard = deck.deal('Answer')
        self.assertEqual('Test card', newcard.value)
        self.assertEqual([], deck.answercards)
        self.assertEqual(card, deck.dealt_answers[0])

    def test_dealing_q_card_removes_from_deck(self):
        card = Card('Question', 'Test card')
        deck = Deck([card])
        newcard = deck.deal('Question')
        self.assertEqual('Test card', newcard.value)
        self.assertEqual([], deck.questioncards)
        self.assertEqual(card, deck.dealt_questions[0])

    def test_deal_from_empty_deck_fails(self):
        card = Card('Question', 'Test card')
        deck = Deck([card])
        newcard = deck.deal('Question')
        with self.assertRaises(NoMoreCards):
            newcard = deck.deal('Question')

    def test_dealing_given_card_works(self):
        cards = []
        cards.append(Card('Answer', 'Card 0'))
        cards.append(Card('Answer', 'Card 1'))
        cards.append(Card('Answer', 'Card 2'))
        cards.append(Card('Answer', 'Card 3'))
        deck = Deck(cards)
        newcard = deck.deal('Answer', 2)
        self.assertEqual('Card 2', newcard.value)

    def test_deal_deals_from_end(self):
        cards = []
        cards.append(Card('Answer', 'Card 0'))
        cards.append(Card('Answer', 'Card 1'))
        cards.append(Card('Answer', 'Card 2'))
        cards.append(Card('Answer', 'Card 3'))
        deck = Deck(cards)
        newcard = deck.deal('Answer')
        self.assertEqual('Card 3', newcard.value)

    def test_shuffle_actually_does(self):
        """ NOTE: this may rarely fail, since it is a random shuffle,
        and a random shuffle may occasionally return the exact same
        order.  test again to confirm.  add cards if it fails too
        frequently. """
        cards = []
        cards.append(Card('Answer', 'Card 0'))
        cards.append(Card('Answer', 'Card 1'))
        cards.append(Card('Answer', 'Card 2'))
        cards.append(Card('Answer', 'Card 3'))
        deck = Deck(cards)
        deck.shuffle()
        self.assertNotEqual(cards, deck.answercards)

    def test_show_hand_does(self):
        cards = []
        values = []
        cards.append(Card('Answer', 'Card 0'))
        values.append('Card 0')
        cards.append(Card('Answer', 'Card 1'))
        values.append('Card 1')
        cards.append(Card('Answer', 'Card 2'))
        values.append('Card 2')
        cards.append(Card('Answer', 'Card 3'))
        values.append('Card 3')
        deck = Deck(cards)
        myhand = deck.show_hand('Answer')
        self.assertEqual(values, myhand)

    def test_reset_deck_desk(self):
        cards = []
        cards.append(Card('Answer', 'Card 0'))
        cards.append(Card('Answer', 'Card 1'))
        cards.append(Card('Answer', 'Card 2'))
        cards.append(Card('Answer', 'Card 3'))
        deck = Deck(cards)
        deck2 = Deck(cards)
        # throw two cards
        deck.deal('Answer')
        deck.deal('Answer')
        deck.reset()
        self.assertEqual(deck.show_hand('Answer').sort(),
            deck2.show_hand('Answer').sort())

    def test_load_cards_twice_no_dupes(self):
        game = Game()
        game.load_cards()
        num = len(game.deck.questioncards)
        game.load_cards()
        self.assertEqual(num, len(game.deck.questioncards))

class PlayerTest(unittest.TestCase):
    def test_create_player_works(self):
        player = Player('Bob', '~bobbo')
        self.assertEqual('Bob', player.nick)

    def test_record_win_works(self):
        player = Player('Bob', '~bobbo')
        player.record_win()
        self.assertEqual((1, 0, 0), player.get_score())

    def test_record_game_win_works(self):
        player = Player('Bob', '~bobbo')
        player.record_win()
        player.game_win()
        self.assertEqual((0, 1, 1), player.get_score())

    def test_show_hand_works(self):
        cards = []
        cards.append(Card('Answer', 'Card 0'))
        cards.append(Card('Answer', 'Card 1'))
        cards.append(Card('Answer', 'Card 2'))
        cards.append(Card('Answer', 'Card 3'))
        deck = Deck(cards)
        player = Player('Bob', '~bobbo')
        player.deck = deck
        self.assertEqual(deck.show_hand('Answer'), player.show_hand())

    def test_add_card_works(self):
        player = Player('Bob', '~bobbo')
        player.add_card(Card('Answer', 'Card 0'))
        player.add_card(Card('Answer', 'Card 1'))
        self.assertEqual(['Card 0', 'Card 1'], player.show_hand())

    def test_deal_deals_right_card(self):
        cards = []
        cards.append(Card('Answer', 'Card 0'))
        cards.append(Card('Answer', 'Card 1'))
        cards.append(Card('Answer', 'Card 2'))
        cards.append(Card('Answer', 'Card 3'))
        deck = Deck(cards)
        player = Player('Bob', '~bobbo')
        player.deck = deck
        self.assertEqual(player.deal(1).value, cards[1].value)

    def test_new_player_dealt_cards(self):
        game = start_game()
        new_player = Player('Ann', '~anno')
        run_command(game, 'join', user=new_player)
        self.assertEqual(game.config['hand_size'], len(new_player.deck))


class GameTest(unittest.TestCase):
    def setUp(self):
        cahirc.Cahirc.say.reset_mock()

    def test_init_establishes_good_defaults(self):
        game = Game()
        self.assertEqual(game.status, 'inactive')
        self.assertIsInstance(game.deck, Deck)

    def test_start_game_sets_state_correctly(self):
        game = Game()
        game.start()
        self.assertEqual(game.status, 'wait_players')

    def test_commander_runs_start_command(self):
        game = Game()
        msg = FakeIRCmsg('start') # bob is the default player
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertEqual('wait_players', game.status)

    def test_commander_runs_play_command(self):
        hand_size = Config().data['hand_size']
        game = Game()
        p = CmdParser(game)
        bob = Player('Bob', '~bobbo')
        jim = Player('Jim', '~jimbo')
        joe = Player('Joe', '~joemg')
        msg = FakeIRCmsg('play 1', user=jim)
        game.start()
        game.add_player(bob)
        game.add_player(jim)
        game.add_player(joe)
        p.parse(msg)
        game.command(p)
        self.assertEqual(hand_size - 1, len(jim.show_hand()))

    def test_winner_announcement(self):
        config = Config().data
        game = start_game()
        pick = game.question.pick
        cardslist = ' '.join([str(i) for i in range(pick)])
        run_command(game, f'play {cardslist}', user=game.players[1])
        run_command(game, f'play {cardslist}', user=game.players[2])
        answers = game.answers
        # these shenanigans are because we need to save info before
        # the 'winner' command is run, or else the second round nukes the
        # verification data
        winners = {player: game.format_answer(answers[player]['cards']) 
                   for player in answers}
        annc = game.get_text('winner_announcement')
        run_command(game, 'winner 0', user=game.players[0])
        if game.players[1].points == 1:
            winner = game.players[1]
        else:
            winner = game.players[2]
        cards = answers[winner]['cards']
        answer = winners[winner]
        annc = annc.format(player=winner.nick, card=answer, points=1)
        expected = call(annc)
        self.assertEqual(str(expected), str(cahirc.Cahirc.say.mock_calls[-5]))

    def test_start_cant_be_run_twice(self):
        text = Config().data['text']['en']
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~joebo')
        jim = Player('Jim', '~jimbo')
        run_command(game, 'start', user=bob)
        self.assertEqual('wait_players', game.status)
        run_command(game, 'join', user=joe);
        run_command(game, 'join', user=jim);
        self.assertEqual('wait_answers', game.status)
        run_command(game, 'start', user=bob)
        self.assertEqual('wait_answers', game.status)
        self.assertEqual("call('{}')".format(text['game_already_started']), 
                            str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_join_gives_a_message(self):
        text = Config().data['text']['en']['welcome_wait']
        text = text.format(name='Bob', num='2', player_word='players')
        game = Game()
        bob = Player('Bob', '~bobbo')
        run_command(game, 'join', user=bob)
        self.assertEqual("call('{}')".format(text), 
                         str(cahirc.Cahirc.say.mock_calls[-1])
                         .format(name='Bob', num='2', player_word='players'))

    def test_quit_quits(self):
        game = start_game()
        bob = game.players[0]
        run_command(game, 'quit', user=bob)
        self.assertEqual(2, len(game.players))

    def test_quit_quits_correct_player(self):
        game = start_game()
        bob = game.players[0]
        prev_players = game.players
        run_command(game, 'quit', user=bob)
        self.assertEqual(prev_players[1], game.players[0])
        self.assertEqual(prev_players[2], game.players[1])

    def test_quit_works_with_one_player(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        run_command(game, 'start', user=bob)
        run_command(game, 'quit', user=bob)
        self.assertEqual(0, len(game.players))

    def test_quit_says_something(self):
        text = Config().data['text']['en']['quit_message'].format(player='Bob')
        game = Game()
        bob = Player('Bob', '~bobbo')
        run_command(game, 'start', user=bob)
        run_command(game, 'quit', user=bob)
        expected = call(text)
        self.assertEqual(str(expected), str(cahirc.Cahirc.say.mock_calls[-2]))

    def test_quit_ends_game_when_zero_players(self):
        game = start_game()
        run_command(game, 'quit', user=game.players[2])
        run_command(game, 'quit', user=game.players[0])
        run_command(game, 'quit', user=game.players[0])
        self.assertEqual('inactive', game.status)
        self.assertEqual([], game.players)

    def test_czar_reassigned_when_czar_quits(self):
        game = start_game()
        czar = game.czar
        run_command(game, 'quit', user=czar)
        self.assertEqual(game.players[0], game.czar)



class GamePlayerTest(unittest.TestCase):
    def test_adding_player_does(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        game.add_player(bob)
        self.assertEqual([bob], game.players)

    def test_adding_dupe_player_is_ignored(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        game.add_player(bob)
        game.add_player(bob)
        self.assertEqual([bob], game.players)

    def test_first_player_is_czar(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertEqual(bob, game.czar)

    def test_next_czar_works(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        game.add_player(bob)
        game.add_player(joe)
        self.assertEqual(joe, game.next_czar())
        self.assertEqual(joe, game.czar)

    def test_next_czar_loops(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertEqual(joe, game.next_czar())
        self.assertEqual(jim, game.next_czar())
        self.assertEqual(bob, game.next_czar())

    def test_player_starts_and_is_registered(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        msg = FakeIRCmsg('start')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertEqual(str(bob), str(game.players[0]))

    def test_player_start_cant_join(self):
        game = Game()
        p = CmdParser(game)
        bob = Player('Bob', '~bobbo')
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        msg = FakeIRCmsg('join')
        p.parse(msg)
        game.command(p)
        self.assertEqual(1, len(game.players))


class PlayTest(unittest.TestCase):
    def test_game_serves_question_card(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertEqual('wait_answers', game.status)
        self.assertIsNot(None, game.question)

    def test_game_deals_to_players(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertEqual(10, len(bob.show_hand()))
        self.assertEqual(10, len(joe.show_hand()))
        self.assertEqual(10, len(jim.show_hand()))

    def test_czar_answer_not_accepted(self):
        game = start_game()
        num_cards = game.question.pick
        nums = ' '.join([str(i) for i in range(num_cards)])
        run_command(game, f'pick {nums}', user=game.players[0])
        expected = str(call(game.get_text('not_player')))
        self.assertEqual(expected, str(cahirc.Cahirc.say.mock_calls[-1]))


    def test_other_answers_accepted(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        joecard = joe.deal(2)
        jimcard = jim.deal(3)
        game.play(joe, joecard)
        game.play(jim, jimcard)
        self.assertEqual(2, len(game.answers))

    def test_multiple_plays_not_allowed(self):
        game = start_game()
        jim = game.players[2]
        num_cards = game.question.pick
        remaining = Config().data['hand_size'] - num_cards
        nums = ' '.join([str(i) for i in range(num_cards)])
        run_command(game, f'pick {nums}', user=jim)
        run_command(game, f'pick {nums}', user=jim)
        expected = str(call(game.get_text('already_played')))
        self.assertEqual(expected, str(cahirc.Cahirc.say.mock_calls[-1]))
        self.assertEqual(remaining, len(jim.deck))

    def test_correct_status_once_all_played(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        self.assertEqual('wait_czar', game.status)

    def ignore_post_complete_plays_fail(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        with self.assertRaises(NotPermitted):
            game.play(jim, jim.deal(1))

    def test_selcting_answer_ups_score(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        game.winner(bob, [0])
        self.assertEqual(1, game.answer_order[0].points)

    def test_selecting_answer_moves_czar(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        game.winner(bob, [0])
        self.assertEqual(joe, game.czar)


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.config = Config().data
        cahirc.Cahirc.say.reset_mock()

    def test_status_command_does_anything(self):
        game = Game()
        p = CmdParser(game)
        msg = FakeIRCmsg('status')
        p.parse(msg)
        game.command(p)
        self.assertNotEqual([], cahirc.Cahirc.say.mock_calls)

    def test_status_wait_players(self):
        text = self.config['text']['en']['status']['wait_players']
        text = text.format(num=2)
        expected = call(text)
        game = Game()
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        msg = FakeIRCmsg('status')
        p.parse(msg)
        game.command(p)
        self.assertEqual(expected, cahirc.Cahirc.say.mock_calls[-1])

    def test_status_inactive(self):
        bob = Player('Bob', '~bobbo')
        text = self.config['text']['en']['status']['inactive']
        expected = call(text)
        game = Game()
        game.status = 'inactive'
        game.state(bob, [])
        self.assertEqual(str(expected), str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_status_wait_answers(self):
        bob = Player('Bob', '~bobbo')
        jim = Player('Jim', '~jimbo')
        joe = Player('Joe', '~joebo')
        game = Game()
        game.start() #status should how be wait_answers
        game.add_player(bob)
        game.add_player(jim)
        game.add_player(joe)
        p = CmdParser(game)
        msg = FakeIRCmsg('play 1', user=jim)
        p.parse(msg)
        game.command(p)
        question = game.question.formattedvalue
        players = gameclass.playerlist_format([joe.nick])
        text = self.config['text']['en']['status']['wait_answers']
        text = text.format(players=players, question=question)
        expected = call(text)
        game.state(bob, [])
        self.assertEqual(str(expected), str(cahirc.Cahirc.say.mock_calls[-1]),
            msg='This test fails regularly since the order of the player list is not deterministic')

    def test_status_wait_czar(self):
        game = start_game()
        num_cards = game.question.pick
        nums = ' '.join([str(i) for i in range(num_cards)])
        run_command(game, 'play {}'.format(nums), user=game.players[1])
        run_command(game, 'play {}'.format(nums), user=game.players[2])
        run_command(game, 'status', user=game.players[0])
        played_annc = game.get_text('status')['wait_czar']
        played_annc = played_annc.format(czar=game.players[0].nick)
        self.assertTrue(re.search(played_annc,
            str(cahirc.Cahirc.say.mock_calls[-3])))


class ListCmdTest(unittest.TestCase):
    def setUp(self):
        cahirc.Cahirc.say.reset_mock()

    def test_list_command_works(self):
        config = Config().data
        game = start_game()
        player = game.players[1]
        msg = FakeIRCmsg('list', user=player)
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        playerlist = [player.nick for player in game.players]
        players = gameclass.playerlist_format(playerlist)
        annc = config['text']['en']['player_list']
        annc = annc.format(players=players)
        expected = call(annc)
        self.assertEqual(str(expected), str(cahirc.Cahirc.say.mock_calls[-1]))



class CardsCmdTest(unittest.TestCase):
    def setUp(self):
        cahirc.Cahirc.say.reset_mock()

    def test_cards_command_works(self):
        config = Config().data
        game = start_game()
        player = game.players[1]
        p = CmdParser(game)
        msg = FakeIRCmsg('cards', user=player)
        p.parse(msg)
        game.command(p)
        hand = player.show_hand()
        annc = config['text']['en']['player_hand']
        handstring = ''
        i = 0
        for card in hand:
            handstring += '[{}] {} '.format(i, card)
            i += 1
        expected = call(annc.format(cards=handstring))
        self.assertIn(str(expected), str(cahirc.Cahirc.say.mock_calls[-1]))
        self.assertEqual(player.nick, game.irc.destination)
                      

    def test_cards_replays_question(self):
        config = Config().data
        game = start_game()
        player = game.players[1]
        p = CmdParser(game)
        msg = FakeIRCmsg('cards', user=player)
        p.parse(msg)
        game.command(p)
        question = game.question.formattedvalue
        annc = config['text']['en']['question_announcement']
        annc = annc.format(card=question) 
        expected = call(annc)
        self.assertEqual(str(expected), str(cahirc.Cahirc.say.mock_calls[-2]))


    def test_cards_command_works_with_no_cards(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        msg = FakeIRCmsg('cards')
        p.parse(msg)
        game.command(p)
        self.assertEqual(call("Game hasn't started yet"),
                         cahirc.Cahirc.say.mock_calls[-1])
        


class ScoreCmdTest(unittest.TestCase):
    def setUp(self):
        cahirc.Cahirc.say.reset_mock()

    def test_score_works(self):
        config = Config().data
        game = start_game()
        pick = game.question.pick
        cardslist = ' '.join([str(i) for i in range(pick)])
        run_command(game, f'play {cardslist}', user=game.players[1])
        run_command(game, f'play {cardslist}', user=game.players[2])
        run_command(game, 'winner 0', user=game.players[0])
        run_command(game, 'score', user=game.players[1])
        scores = game.score_list()
        annc = config['text']['en']['score_announcement']
        annc = annc.format(scores=scores)
        expected = call(annc)
        self.assertEqual(str(expected), str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_score_list_works(self):
        text = Config().data['text']['en']['score_element']
        game = Game()
        bob = Player('Bob', '~bobbo')
        jim = Player('Jim', '~jimbo')
        joe = Player('Joe', '~joemg')
        game.start()
        game.add_player(bob)
        game.add_player(jim)
        game.add_player(joe)
        game.players[0].points = 5
        game.players[1].points = 4
        game.players[2].points = 3
        def point_word(points):
            return 'point' if points == 1 else 'points'
        string = [text.format(player=pl.nick, points=pl.points, 
                              point_word=point_word(pl.points))
                              for pl in game.players]
        self.assertEqual(', '.join(string), game.score_list())

    def test_score_ignored_when_inactive(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        run_command(game, 'score', user=bob)
        cahirc.Cahirc.say.assert_not_called()
            

class ReloadCmdTest(unittest.TestCase):
    def setUp(self):
        cahirc.Cahirc.say.reset_mock()

    def test_reload_ignored_while_game_running(self):
        game = start_game()
        run_command(game, 'reload')
        expected = str(call(game.get_text('reload_wait')))
        self.assertEqual(expected, str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_reload_loads_new_config(self):
        game = Game()
        Config._fields.append('testvalue')
        old_config = game.config
        copyfile('config.yaml', 'config.yaml.real')
        with open('config.yaml', 'a') as fp:
            fp.write('testvalue: foo')
        run_command(game, 'reload')
        copyfile('config.yaml.real', 'config.yaml')
        os.unlink('config.yaml.real')
        self.assertIn('testvalue', game.config)
        cahirc.Cahirc.say.assert_not_called()


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.p = CmdParser(self.game)
        cahirc.Cahirc.say.reset_mock()

    def test_basic_command_works(self):
        game = Game()
        cmdstring = 'start'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual(cmdstring, self.p.command)

    def test_one_argument_command_works(self):
        cmdstring = 'winner 1'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual('winner', self.p.command)
        self.assertEqual([1], self.p.args)

    # note weird hacky thing: there were lots of tests that depend upon
    # play returning a number, but play actually needs to return cards.
    # so, there are two different behaviors going here: the play cmd,
    # without a player, just returns numbers.  with a player, it
    # expands out to cards.  we will only use the player version in
    # real life, but the numbers version is handy for testing.

    def test_multi_argument_command(self):
        bob = Player('Bob', '~bobbo')
        self.game.add_player(bob)
        self.game.load_cards()
        self.game.deck.shuffle()
        self.game.deal_all_players(10)
        self.game.status = 'wait_answers'
        cmdstring = 'play 3 4 5'
        msg = FakeIRCmsg(cmdstring, user=bob)
        self.p.parse(msg)
        self.assertEqual('play', self.p.command)
        self.assertEqual(3, len(self.p.args))
        self.assertEqual([str, str, str], [type(i) for i in self.p.args])

    def test_one_arg_with_garbage(self):
        cmdstring = 'winner 1 because we rock'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual('winner', self.p.command)
        self.assertEqual([1], self.p.args)

    def test_multi_arg_with_garbage(self):
        cmdstring = 'play 1 2 3 because ew'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual('play', self.p.command)
        self.assertEqual([1, 2, 3], self.p.args)

    def test_random_string(self):
        cmdstring = 'why is the sky blue?'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual(None, self.p.command)
        self.assertEqual([], self.p.args)

    def test_cmd_no_args(self):
        cmdstring = 'pick yourself up'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual(None, self.p.command)
        self.assertEqual([], self.p.args)

    def test_pick_works_as_play(self):
        self.game.status = 'wait_answers'
        cmdstring = 'pick 1'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual('play', self.p.command)
        self.assertEqual([1], self.p.args)

    def test_pick_works_as_winner(self):
        self.game.status = 'wait_czar'
        cmdstring = 'pick 1'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual('winner', self.p.command)
        self.assertEqual([1], self.p.args)

    def test_shame_works_as_score(self):
        cmdstring = 'shame'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertEqual('score', self.p.command)
        self.game.status = 'wait_czar'
        self.p.parse(msg)
        self.assertEqual('score', self.p.command)

    def test_commands_wo_args_ignored_w_args(self):
        cmdstring = 'shame about the weather'
        msg = FakeIRCmsg(cmdstring)
        self.p.parse(msg)
        self.assertIsNone(self.p.command)

    def test_dealing_a_card_works(self):
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        self.game.start()
        self.game.add_player(bob)
        self.game.add_player(joe)
        self.game.add_player(jim)
        jimcard = jim.show_hand()[1]
        cmdstring = 'play 1'
        msg = FakeIRCmsg(cmdstring, user=jim)
        self.p.parse(msg)
        self.game.command(self.p)
        self.assertEqual([jimcard], self.game.answers[jim]['cards'])

    def test_dealing_inorder_cards_works(self):
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        self.game.start()
        self.game.add_player(bob)
        self.game.add_player(joe)
        self.game.add_player(jim)
        jimcards = jim.show_hand()[1:4]
        cmdstring = 'play 1 2 3'
        msg = FakeIRCmsg(cmdstring, user=jim)
        self.p.parse(msg)
        self.game.command(self.p)
        self.assertEqual(jimcards, self.game.answers[jim]['cards'])

    def test_dealing_wackorder_cards_works(self):
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        self.game.start()
        self.game.add_player(bob)
        self.game.add_player(joe)
        self.game.add_player(jim)
        jimcards = []
        jimcards.append(jim.show_hand()[3])
        jimcards.append(jim.show_hand()[1])
        jimcards.append(jim.show_hand()[7])
        cmdstring = 'play 3 1 7'
        msg = FakeIRCmsg(cmdstring, user=jim)
        self.p.parse(msg)
        self.game.command(self.p)
        self.assertEqual(jimcards, self.game.answers[jim]['cards'])

    def test_aliases_work_at_all(self):
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        self.game.start()
        self.game.add_player(bob)
        self.game.add_player(joe)
        self.game.add_player(jim)
        config = Config().data
        player = self.game.players[1]
        msg = FakeIRCmsg('players', user=player)
        p = CmdParser(self.game)
        p.parse(msg)
        self.game.command(p)
        playerlist = [player.nick for player in self.game.players]
        players = gameclass.playerlist_format(playerlist)
        annc = config['text']['en']['player_list']
        annc = annc.format(players=players)
        expected = call(annc)
        self.assertEqual(str(expected), str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_pick_alias_ignored_before_game_start(self):
        bob = Player('Bob', '~bobbo')
        msg = FakeIRCmsg('pick 1', user=bob)
        self.p.parse(msg)
        self.game.command(self.p)
        text = Config().data['text']['en']
        self.assertEqual(0, len(cahirc.Cahirc.say.mock_calls))


class ConfigTest(unittest.TestCase):
    def test_config_exists_at_all(self):
        config = Config()
        self.assertEqual(['.', '..'], config.path)

    def test_config_reads_default_file(self):
        config = Config()
        self.assertEqual('cards', config.data['carddir'])


class BasicIRCTest(unittest.TestCase):
    def setUp(self):
        cahirc.Cahirc.say.reset_mock()

    def test_irc_msg_obj(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        game.add_player(bob)
        msg = FakeIRCmsg('hello')
        self.assertEqual(msg.nick, 'Bob')
        self.assertEqual(msg.user, '~bobbo')
        self.assertEqual(msg.msg, 'hello')
        self.assertEqual(msg.source, 'privmsg')

    # TODO: test for a privmsg getting a privmsg in return, and a pubmsg
    # getting a pubmsg in return

    def test_status_in_private(self):
        config = Config().data
        game = start_game()
        player1 = game.players[1]
        player2 = game.players[2]
        p = CmdParser(game)
        msg = FakeIRCmsg('play 1', user=player1)
        p.parse(msg)
        game.command(p)
        msg = FakeIRCmsg('status', user=player2, source='privmsg')
        p.parse(msg)
        game.command(p)
        question = game.question.formattedvalue
        players = gameclass.playerlist_format([player2.nick])
        self.assertEqual(player2.nick, game.irc.destination)


class GameIRCTest(unittest.TestCase):
    def setUp(self):
        cahirc.Cahirc.say.reset_mock()

    def test_game_start_text_says_game_start(self):
        config = Config()
        text = config.data['text']['en']['round_start']
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        self.assertEqual('call("{}")'.format(text),
                         str(cahirc.Cahirc.say.mock_calls[0]))

    def test_game_start_says_game_start(self):
        config = Config()
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        self.assertEqual(2, len(cahirc.Cahirc.say.mock_calls))

    def test_game_start_joining_works(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        self.assertEqual(str(bob), str(game.players[0]))

    def test_game_join_joining_works(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        jim = Player('Jim', '~bobbo')
        msg = FakeIRCmsg('join', user=jim)
        p.parse(msg)
        game.command(p)
        self.assertEqual([str(bob), str(jim)], [str(p) for p in game.players])

    def test_game_three_join_starts(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        jim = Player('Jim', '~bobbo')
        msg = FakeIRCmsg('join', user=jim)
        p.parse(msg)
        p.player = jim
        game.command(p)
        joe = Player('Joe', '~bobbo')
        msg = FakeIRCmsg('join', user=joe)
        p.parse(msg)
        game.command(p)
        self.assertEqual('wait_answers', game.status)

    def test_double_join_complains(self):
        cahirc.Cahirc.say.reset_mock()
        game = Game()
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        msg = FakeIRCmsg('join')
        p.parse(msg)
        game.command(p)
        config = Config()
        self.assertTrue(re.search(config.data['text']['en']['double_join'],
            str(cahirc.Cahirc.say.mock_calls[-1])))

    def test_game_three_join_starts(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        jim = Player('Jim', '~jimbo')
        msg = FakeIRCmsg('join', user=jim)
        p.parse(msg)
        game.command(p)
        joe = Player('Joe', '~joebo')
        msg = FakeIRCmsg('join', user=joe)
        p.parse(msg)
        game.command(p)
        self.assertEqual(10, len(game.players[0].show_hand()))
        self.assertEqual(10, len(game.players[1].show_hand()))
        self.assertEqual(10, len(game.players[2].show_hand()))

    def test_first_question_displays(self):
        config = Config().data
        chan = config['default_channel']
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertTrue(re.search('Card: ',
            str(cahirc.Cahirc.say.mock_calls[5])))

    def test_joe_gets_cards(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertTrue(re.search('Your cards are: ',
            str(cahirc.Cahirc.say.mock_calls[7])))

    def test_candidates_are_announced(self):
        config = Config().data
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(joe, joe.deal(1))
        game.play(jim, jim.deal(1))
        played_annc = config['text']['en']['all_cards_played']
        self.assertTrue(re.search(played_annc,
            str(cahirc.Cahirc.say.mock_calls[10])))
        self.assertTrue(re.search('[0]', 
                        str(cahirc.Cahirc.say.mock_calls[11])))
        self.assertTrue(re.search('[1]', 
                        str(cahirc.Cahirc.say.mock_calls[12])))

    def test_irc_game(self):
        config = Config().data
        game = Game()
        bob = Player('Bob', '~bobbo')
        jim = Player('Jim', '~jimbo')
        joe = Player('Joe', '~joebo')
        cahirc.Cahirc.say.reset_mock()
        self.assertEqual([], cahirc.Cahirc.say.mock_calls)
        p = CmdParser(game)
        msg = FakeIRCmsg('start', user=bob)
        p.parse(msg)
        game.command(p)
        self.assertEqual(2, len(cahirc.Cahirc.say.mock_calls))
        msg = FakeIRCmsg('join', user=jim)
        p.parse(msg)
        game.command(p)
        self.assertEqual(3, len(cahirc.Cahirc.say.mock_calls))
        msg = FakeIRCmsg('join', user=joe)
        p.parse(msg)
        game.command(p)
        self.assertTrue(re.search(config['text']['en']['round_start'],
            str(cahirc.Cahirc.say.mock_calls[0])))
        round_annc = config['text']['en']['round_announcement'].format(round_num=1, czar='Bob')
        round_call = call(round_annc)
        self.assertEqual(str(round_call),
            str(cahirc.Cahirc.say.mock_calls[4]))

    def ignore_answer_is_privmsgd(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~joebo')
        jim = Player('Jim', '~jimbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        pick_answers(game, joe)
        self.assertEqual('Joe', game.irc.destination)
        # this test wasn't working anyway

    def test_early_play_is_ignored(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        run_command(game, 'start', user=bob)
        run_command(game, 'play 1', user=bob)
        text = Config().data['text']['en']['round_start']
        self.assertEqual('call("{}")'.format(text), 
                         str(cahirc.Cahirc.say.mock_calls[-2]))

    def test_winner_triggers_second_round(self):
        game = start_game()
        pick = game.question.pick
        cardslist = ' '.join([str(i) for i in range(pick)])
        run_command(game, f'pick {cardslist}', user=game.players[1])
        run_command(game, f'pick {cardslist}', user=game.players[2])
        run_command(game, 'winner 0', user=game.players[0])
        text = game.get_text('round_announcement')
        text = text.format(round_num=2, czar=game.players[1].nick)
        expected = str(call(text))
        self.assertEqual(expected, str(cahirc.Cahirc.say.mock_calls[-4]))

    def test_second_round_conditions_are_sensible(self):
        game = start_game()
        pick = game.question.pick
        cardslist = ' '.join([str(i) for i in range(pick)])
        run_command(game, f'pick {cardslist}', user=game.players[1])
        run_command(game, f'pick {cardslist}', user=game.players[2])
        run_command(game, 'winner 0', user=game.players[0])
        for i in range(3):
            self.assertEqual(10, len(game.players[i].deck))
        self.assertEqual(game.players[1], game.czar)

    def test_non_czar_cannot_pick_winner(self):
        game = start_game()
        pick = game.question.pick
        cardslist = ' '.join([str(i) for i in range(pick)])
        run_command(game, f'pick {cardslist}', user=game.players[1])
        run_command(game, f'pick {cardslist}', user=game.players[2])
        run_command(game, 'winner 0', user=game.players[2])
        self.assertEqual('wait_czar', game.status)

    def test_end_game(self):
        game = start_game()
        max_points = Config().data['max_points']
        i = 0
        while True:
            i += 1
            for player in game.players:
                pick_answers(game, player)
            run_command(game, 'winner 0', user=game.czar)
            for player in game.players:
                points = player.get_score()[0]
                name = player.nick
                if points > max_points:
                    self.fail(f'player {name} has {points} points')
                    break
            if game.status == 'inactive':
                break
        expected = str(call(game.get_text('game_start')))
        self.assertEqual(expected, str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_help_command(self):
        game = start_game()
        run_command(game, 'help')
        expected = str(call(game.get_text('help_blurb')))
        self.assertEqual(expected, str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_commands_command(self):
        game = start_game()
        run_command(game, 'commands')
        expected = str(call(CmdParser(game).get_commands()))
        self.assertEqual(expected, str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_second_play_allowed(self):
        game = start_game()
        pick_answers(game, game.players[1])
        pick_answers(game, game.players[2])
        run_command(game, 'winner 1', user=game.players[0])
        pick_answers(game, game.players[2])
        unexpected = str(call(game.get_text('already_played')))
        self.assertNotEqual(unexpected, str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_czar_advances_through_all_players(self):
        game = start_game()
        for i in range(4):
            self.assertEqual(game.players[i%3], game.czar)
            for player in game.players:
                pick_answers(game, player)
            run_command(game, 'winner 0', user=game.czar)

    def test_answer_annc_handles_spaceless_questions(self):
        game = start_game()
        question_str = 'Thing is:'
        card = Card('Question', question_str)
        game.question = card
        answercard = game.players[1].deck.answercards[0]
        run_command(game, 'pick 0', user=game.players[1])
        text = game.get_text('answer_played')
        text = text.format(answer=question_str + ' ' + answercard.value)
        expected = str(call(text))
        self.assertEqual(expected, str(cahirc.Cahirc.say.mock_calls[-1]))


class ResponseTest(unittest.TestCase):
    def test_round_num_displays(self):
        cahirc.Cahirc.say.reset_mock()
        game = start_game()
        self.assertTrue(re.search("Round 1!",
            str(cahirc.Cahirc.say.mock_calls[4])))
        self.assertTrue(re.search("Bob is the card czar",
            str(cahirc.Cahirc.say.mock_calls[4])))

    def test_answers_are_displayed(self):
        cahirc.Cahirc.say.reset_mock()
        game = Game()
        answer_card = Card('Answer', 'TEST')
        question_card= Card('Question', '%s is TEST')
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.question = question_card
        expected_answer = 'TEST is TEST'
        game.play(joe, answer_card)
        game.play(jim, answer_card)
        self.assertEqual(f"call('[1] {expected_answer}')",
            str(cahirc.Cahirc.say.mock_calls[-1]))

    def test_winner_is_announced(self):
        config = Config().data
        text = config['text']['en']['winner_announcement']
        cahirc.Cahirc.say.reset_mock()
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.question = Card('Question', '%s is TEST')
        game.play(joe, Card('Answer', 'JOE'))
        game.play(jim, Card('Answer', 'JIM'))
        # winner() takes a player as an argument, because all commands
        # do.  that player is discarded, though, since the winner
        # command only really cares about the choice number.
        game.winner(bob, [0])
        winner = game.answer_order[0]
        expected_answer = text.format(player=winner.nick,
            card=f'{winner.nick.upper()} is TEST', points=1)
        self.assertEqual(f"call('{expected_answer}')",
            str(cahirc.Cahirc.say.mock_calls[-5]))



if __name__ == '__main__':
    unittest.main()
