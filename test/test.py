#!/usr/bin/env python3
# vi:set expandtab ai wm=0:
# pylint: disable=missing-docstring


import unittest, sys, os, re
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call
import irc.client

sys.path.append('..')
sys.path.append('.')

from config import Config
from card import Card
from deck import Deck
from player import Player
import game as gameclass
from game import Game
from game import cahirc
from cmdparser import CmdParser
from exceptions import (NotPermitted, NoMoreCards)
from cahirc import IRCmsg, FakeIRCmsg

cahirc.Cahirc.say = MagicMock()

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


class GameTest(unittest.TestCase):
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
        self.assertEqual(9, len(jim.show_hand()))


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
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        with self.assertRaises(NotPermitted):
            game.play(bob, bob.deal(1))

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
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        with self.assertRaises(NotPermitted):
            game.play(jim, jim.deal(1))

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

    def test_post_complete_plays_fail(self):
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
        game.winner(bob, 0)
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
        game.winner(bob, 0)
        self.assertEqual(joe, game.czar)


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.p = CmdParser(self.game)

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
        cmdstring = 'play 3 4 5'
        msg = FakeIRCmsg(cmdstring, user=bob)
        self.p.parse(msg)
        self.assertEqual('play', self.p.command)
        #self.assertEqual([3, 4, 5], self.p.args)
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


class ConfigTest(unittest.TestCase):
    def test_config_exists_at_all(self):
        config = Config()
        self.assertEqual(['.', '..'], config.path)

    def test_config_reads_default_file(self):
        config = Config()
        self.assertEqual('cards', config.data['carddir'])


class BasicIRCTest(unittest.TestCase):
    def test_irc_msg_obj(self):
        game = Game()
        bob = Player('Bob', '~bobbo')
        game.add_player(bob)
        msg = FakeIRCmsg('hello')
        self.assertEqual(msg.nick, 'Bob')
        self.assertEqual(msg.user, '~bobbo')
        self.assertEqual(msg.msg, 'hello')
        self.assertEqual(msg.source, 'privmsg')


class GameIRCTest(unittest.TestCase):
    def setUp(self):
        cahirc.Cahirc.say.reset_mock()

    def test_game_start_says_game_start(self):
        config = Config()
        chan = config.data['default_channel']
        text = config.data['text']['en']['round_start']
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        cahirc.Cahirc.say.assert_called_with(chan, text)

    def test_game_start_says_game_start(self):
        config = Config()
        game = Game()
        bob = Player('Bob', '~bobbo')
        p = CmdParser(game)
        msg = FakeIRCmsg('start')
        p.parse(msg)
        game.command(p)
        self.assertEqual(1, len(cahirc.Cahirc.say.mock_calls))

    def test_game_start_joining_works(self):
        game = Game()
        # a person who says something on the channel is registered as a
        # Player for this exact situation
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
            str(cahirc.Cahirc.say.mock_calls[1])))

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
            str(cahirc.Cahirc.say.mock_calls[2])))

    def test_joe_gets_cards(self):
        cahirc.Cahirc.say.reset_mock()
        config = Config().data
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertTrue(re.search('Your cards are: ',
            str(cahirc.Cahirc.say.mock_calls[3])))

    def test_candidates_are_announced(self):
        cahirc.Cahirc.say.reset_mock()
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
            str(cahirc.Cahirc.say.mock_calls[5])))

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
        self.assertEqual(1, len(cahirc.Cahirc.say.mock_calls))
        msg = FakeIRCmsg('join', user=jim)
        p.parse(msg)
        game.command(p)
        self.assertEqual(1, len(cahirc.Cahirc.say.mock_calls))
        msg = FakeIRCmsg('join', user=joe)
        p.parse(msg)
        game.command(p)
        self.assertTrue(re.search(config['text']['en']['round_start'],
            str(cahirc.Cahirc.say.mock_calls[0])))
        round_annc = config['text']['en']['round_announcement'].format(round_num=1, czar='Bob')
        round_call = call('\\#test', round_annc)
        self.assertEqual(str(round_call),
            str(cahirc.Cahirc.say.mock_calls[1]))


    def test_receive_irc(self):
        game = Game()



class ResponseTest(unittest.TestCase):
    def test_round_num_displays(self):
        cahirc.Cahirc.say.reset_mock()
        game = Game()
        bob = Player('Bob', '~bobbo')
        joe = Player('Joe', '~bobbo')
        jim = Player('Jim', '~bobbo')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertTrue(re.search("Round 1!",
            str(cahirc.Cahirc.say.mock_calls[1])))
        self.assertTrue(re.search("Bob is the card czar",
            str(cahirc.Cahirc.say.mock_calls[1])))

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
        self.assertEqual(f"call('\\\\#test', '{expected_answer}')",
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
        game.winner(bob, 0)
        winner = game.answer_order[0]
        expected_answer = text.format(player=winner.nick,
            card=f'{winner.nick.upper()} is TEST', points=1)
        self.assertEqual(f"call('\\\\#test', '{expected_answer}')",
            str(cahirc.Cahirc.say.mock_calls[-1]))


if __name__ == '__main__':
    unittest.main()
