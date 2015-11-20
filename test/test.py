#!/usr/bin/env python
# vi:set expandtab ai:

import unittest, sys

sys.path.append('..')

from card import Card
from deck import Deck
from player import Player
from game import Game
from cmdparser import CmdParser

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
        with self.assertRaises(IndexError):
            newcard = deck.deal('Question')

    def test_adding_answer_gives_no_questions(self):
        card = Card('Answer', 'Test card')
        deck = Deck()
        deck.add(card)
        with self.assertRaises(IndexError):
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
        with self.assertRaises(IndexError):
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
        player = Player('Bob')
        self.assertEqual('Bob', player.name)

    def test_record_win_works(self):
        player = Player('Bob')
        player.record_win()
        self.assertEqual((1, 0, 0), player.get_score())

    def test_record_game_win_works(self):
        player = Player('Bob')
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
        player = Player('Bob')
        player.deck = deck
        self.assertEqual(deck.show_hand('Answer'), player.show_hand())

    def test_add_card_works(self):
        player = Player('Bob')
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
        player = Player('Bob')
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


class ParserTest(unittest.TestCase):
    def test_basic_command_works(self):
        game = Game()
        cmdstring = 'start'
        p = CmdParser(cmdstring, game)
        self.assertEqual('start', p.command)

    def test_one_argument_command_works(self):
        game = Game()
        cmdstring = 'winner 1'
        p = CmdParser(cmdstring, game)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)

    def test_multi_argument_command(self):
        game = Game()
        cmdstring = 'play 3 4 5'
        p = CmdParser(cmdstring, game)
        self.assertEqual('play', p.command)
        self.assertEqual([3, 4, 5], p.args)

    def test_one_arg_with_garbage(self):
        game = Game()
        cmdstring = 'winner 1 because we rock'
        p = CmdParser(cmdstring, game)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)

    def test_multi_arg_with_garbage(self):
        game = Game()
        cmdstring = 'play 1 2 3 because ew'
        p = CmdParser(cmdstring, game)
        self.assertEqual('play', p.command)
        self.assertEqual([1, 2, 3], p.args)

    def test_random_string(self):
        game = Game()
        cmdstring = 'why is the sky blue?'
        p = CmdParser(cmdstring, game)
        self.assertEqual(None, p.command)
        self.assertEqual([], p.args)

    def test_cmd_no_args(self):
        game = Game()
        cmdstring = 'pick yourself up'
        p = CmdParser(cmdstring, game)
        self.assertEqual(None, p.command)
        self.assertEqual([], p.args)

    def test_pick_works_as_play(self):
        game = Game()
        game.status = 'wait_answers'
        cmdstring = 'pick 1'
        p = CmdParser(cmdstring, game)
        self.assertEqual('play', p.command)
        self.assertEqual([1], p.args)

    def test_pick_works_as_winner(self):
        game = Game()
        game.status = 'wait_czar'
        cmdstring = 'pick 1'
        p = CmdParser(cmdstring, game)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)


if __name__ == '__main__':
    unittest.main()
