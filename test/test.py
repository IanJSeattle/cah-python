#!/usr/bin/env python3
# vi:set expandtab ai:

import unittest, sys, os
from unittest.mock import MagicMock, patch

sys.path.append('..')
sys.path.append('.')

from config import Config
from card import Card
from deck import Deck
from player import Player
import game as gameclass
from cmdparser import CmdParser

gameclass.cahirc.IRCBot.say = MagicMock()

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
        game = gameclass.Game()
        self.assertEqual(game.status, 'inactive')
        self.assertIsInstance(game.deck, Deck)

    def test_start_game_sets_state_correctly(self):
        game = gameclass.Game()
        game.start()
        self.assertEqual(game.status, 'wait_players')

    def test_commander_runs_start_command(self):
        game = gameclass.Game()
        p = CmdParser('start', game)
        game.command(p)
        self.assertEqual('wait_players', game.status)

    def test_commander_runs_play_command(self):
        game = gameclass.Game()
        bob = Player('Bob')
        jim = Player('Jim')
        joe = Player('Joe')
        game.start()
        game.add_player(bob)
        game.add_player(jim)
        game.add_player(joe)
        p = CmdParser('play 1', game, jim)
        game.command(p)
        self.assertEqual(9, len(jim.show_hand()))


class GamePlayerTest(unittest.TestCase):
    def test_adding_player_does(self):
        game = gameclass.Game()
        bob = Player('Bob')
        game.add_player(bob)
        self.assertEqual([bob], game.players)

    def test_adding_dupe_player_is_ignored(self):
        game = gameclass.Game()
        bob = Player('Bob')
        game.add_player(bob)
        game.add_player(bob)
        self.assertEqual([bob], game.players)

    def test_first_player_is_czar(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertEqual(bob, game.czar)

    def test_next_czar_works(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        game.add_player(bob)
        game.add_player(joe)
        self.assertEqual(joe, game.next_czar())
        self.assertEqual(joe, game.czar)

    def test_next_czar_loops(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertEqual(joe, game.next_czar())
        self.assertEqual(jim, game.next_czar())
        self.assertEqual(bob, game.next_czar())


class PlayTest(unittest.TestCase):
    def test_game_serves_question_card(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertEqual('wait_answers', game.status)
        self.assertIsNot(None, game.question)

    def test_game_deals_to_players(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertEqual(10, len(bob.show_hand()))
        self.assertEqual(10, len(joe.show_hand()))
        self.assertEqual(10, len(jim.show_hand()))

    def test_czar_answer_not_accepted(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        with self.assertRaises(RuntimeError):
            game.play(bob, bob.deal(1))

    def test_other_answers_accespted(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
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
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        with self.assertRaises(RuntimeError):
            game.play(jim, jim.deal(1))

    def test_correct_status_once_all_played(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        self.assertEqual('wait_czar', game.status)

    def test_post_complete_plays_fail(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        with self.assertRaises(RuntimeError):
            game.play(jim, jim.deal(1))

    def test_selcting_answer_ups_score(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        game.winner(joe)
        self.assertEqual(1, joe.game_wins)
        
    def test_selecting_answer_moves_czar(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        game.winner(jim)
        self.assertEqual(joe, game.czar)


class ParserTest(unittest.TestCase):
    def test_basic_command_works(self):
        game = gameclass.Game()
        cmdstring = 'start'
        p = CmdParser(cmdstring, game)
        self.assertEqual('start', p.command)

    def test_one_argument_command_works(self):
        game = gameclass.Game()
        cmdstring = 'winner 1'
        p = CmdParser(cmdstring, game)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)

    # note weird hacky thing: there were lots of tests that depend upon
    # play returning a number, but play actually needs to return cards.
    # so, there are two different behaviors going here: the play cmd,
    # without a player, just returns numbers.  with a player, it
    # expands out to cards.  we will only use the player version in
    # real life, but the numbers version is handy for testing.

    def test_multi_argument_command(self):
        game = gameclass.Game()
        cmdstring = 'play 3 4 5'
        p = CmdParser(cmdstring, game)
        self.assertEqual('play', p.command)
        self.assertEqual([3, 4, 5], p.args)

    def test_one_arg_with_garbage(self):
        game = gameclass.Game()
        cmdstring = 'winner 1 because we rock'
        p = CmdParser(cmdstring, game)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)

    def test_multi_arg_with_garbage(self):
        game = gameclass.Game()
        cmdstring = 'play 1 2 3 because ew'
        p = CmdParser(cmdstring, game)
        self.assertEqual('play', p.command)
        self.assertEqual([1, 2, 3], p.args)

    def test_random_string(self):
        game = gameclass.Game()
        cmdstring = 'why is the sky blue?'
        p = CmdParser(cmdstring, game)
        self.assertEqual(None, p.command)
        self.assertEqual([], p.args)

    def test_cmd_no_args(self):
        game = gameclass.Game()
        cmdstring = 'pick yourself up'
        p = CmdParser(cmdstring, game)
        self.assertEqual(None, p.command)
        self.assertEqual([], p.args)

    def test_pick_works_as_play(self):
        game = gameclass.Game()
        game.status = 'wait_answers'
        cmdstring = 'pick 1'
        p = CmdParser(cmdstring, game)
        self.assertEqual('play', p.command)
        self.assertEqual([1], p.args)

    def test_pick_works_as_winner(self):
        game = gameclass.Game()
        game.status = 'wait_czar'
        cmdstring = 'pick 1'
        p = CmdParser(cmdstring, game)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)

    def test_shame_works_as_score(self):
        game = gameclass.Game()
        cmdstring = 'shame'
        p = CmdParser(cmdstring, game)
        self.assertEqual('score', p.command)
        game.status = 'wait_czar'
        p.parse(cmdstring)
        self.assertEqual('score', p.command)

    def test_dealing_a_card_works(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        jimcard = jim.show_hand()[1]
        cmdstring = 'play 1'
        p = CmdParser(cmdstring, game, jim)
        game.command(p)
        self.assertEqual([jimcard], game.answers[jim])

    def test_dealing_inorder_cards_works(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        jimcards = jim.show_hand()[1:4]
        cmdstring = 'play 1 2 3'
        p = CmdParser(cmdstring, game, jim)
        game.command(p)
        self.assertEqual(jimcards, game.answers[jim])

    def test_dealing_wackorder_cards_works(self):
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        jimcards = []
        jimcards.append(jim.show_hand()[3])
        jimcards.append(jim.show_hand()[1])
        jimcards.append(jim.show_hand()[7])
        cmdstring = 'play 3 1 7'
        p = CmdParser(cmdstring, game, jim)
        game.command(p)
        self.assertEqual(jimcards, game.answers[jim])


class ConfigTest(unittest.TestCase):
    def test_config_exists_at_all(self):
        config = Config()
        self.assertEqual(['.', '..'], config.path)

    def test_config_reads_default_file(self):
        config = Config()
        self.assertEqual('cards', config.data['carddir'])


class GameIRCTest(unittest.TestCase):
    def test_game_start_says_game_start(self):
        config = Config()
        chan = config.data['default_channel']
        text = config.data['text']['en']['round_start']
        game = gameclass.Game()
        bob = Player('Bob')
        p = CmdParser('start', game, bob)
        game.command(p)
        gameclass.cahirc.IRCBot.say.assert_called_with(chan, text)

    def test_game_start_joining_works(self):
        game = gameclass.Game()
        # a person who says something on the channel is registered as a
        # Player for this exact situation
        bob = Player('Bob')
        p = CmdParser('start', game, bob)
        game.command(p)
        self.assertEqual([bob], game.players)

    def test_game_join_joining_works(self):
        game = gameclass.Game()
        bob = Player('Bob')
        p = CmdParser('start', game, bob)
        game.command(p)
        jim = Player('Jim')
        p.parse('join')
        p.player = jim
        game.command(p)
        self.assertEqual([bob, jim], game.players)

    def test_game_three_join_starts(self):
        game = gameclass.Game()
        bob = Player('Bob')
        p = CmdParser('start', game, bob)
        game.command(p)
        jim = Player('Jim')
        p.parse('join')
        p.player = jim
        game.command(p)
        joe = Player('Joe')
        p.parse('join')
        p.player = joe
        game.command(p)
        self.assertEqual('wait_answers', game.status)

    def test_game_three_join_starts(self):
        game = gameclass.Game()
        bob = Player('Bob')
        p = CmdParser('start', game, bob)
        game.command(p)
        jim = Player('Jim')
        p.parse('join')
        p.player = jim
        game.command(p)
        joe = Player('Joe')
        p.parse('join')
        p.player = joe
        game.command(p)
        print(joe.show_hand())
        self.assertEqual(10, len(joe.show_hand()))


if __name__ == '__main__':
    unittest.main()
