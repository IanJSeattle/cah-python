#!/usr/bin/env python
# vi:set expandtab ai:

import unittest, sys, os, re
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

sys.path.append('..')
sys.path.append('.')

from config import Config
from card import Card
from deck import Deck
from player import Player
import game as gameclass
from cmdparser import CmdParser
from chat import CAHmsg
from exceptions import NoMoreCards

gameclass.chat.Chat.say = MagicMock()
gameclass.chat.Chat.start = MagicMock()

def setup_basic_game():
    game = gameclass.Game()
    bob = Player('Bob')
    joe = Player('Joe')
    jim = Player('Jim')
    game.start()
    game.add_player(bob)
    game.add_player(joe)
    game.add_player(jim)
    return game, bob, joe, jim


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
        player = Player('Bob')
        self.assertEqual('Bob', player.nick)

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
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertEqual('wait_players', game.status)

    def test_commander_runs_play_command(self):
        game = gameclass.Game()
        game, bob, joe, jim = setup_basic_game()
        cmdstring = 'play 1'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
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
        game, bob, joe, jim = setup_basic_game()
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
        game, bob, joe, jim = setup_basic_game()
        self.assertEqual(joe, game.next_czar())
        self.assertEqual(jim, game.next_czar())
        self.assertEqual(bob, game.next_czar())


class PlayTest(unittest.TestCase):
    def test_game_serves_question_card(self):
        game, bob, joe, jim = setup_basic_game()
        self.assertEqual('wait_answers', game.status)
        self.assertIsNot(None, game.question)

    def test_game_deals_to_players(self):
        game, bob, joe, jim = setup_basic_game()
        self.assertEqual(10, len(bob.show_hand()))
        self.assertEqual(10, len(joe.show_hand()))
        self.assertEqual(10, len(jim.show_hand()))

    def test_czar_answer_not_accepted(self):
        game, bob, joe, jim = setup_basic_game()
        with self.assertRaises(RuntimeError):
            game.play(bob, bob.deal(1))

    def test_other_answers_accespted(self):
        game, bob, joe, jim = setup_basic_game()
        joecard = joe.deal(2)
        jimcard = jim.deal(3)
        game.play(joe, joecard)
        game.play(jim, jimcard)
        self.assertEqual(2, len(game.answers))
        
    def test_multiple_plays_not_allowed(self):
        game, bob, joe, jim = setup_basic_game()
        jim_hand = jim.show_hand()
        pick = game.question.pick
        cards = [jim.deal(num) for num in range(pick)]
        game.play(jim, cards)
        with self.assertRaises(RuntimeError):
            game.play(jim, cards)

    def test_correct_status_once_all_played(self):
        game, bob, joe, jim = setup_basic_game()
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        self.assertEqual('wait_czar', game.status)

    def test_post_complete_plays_fail(self):
        game, bob, joe, jim = setup_basic_game()
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        with self.assertRaises(RuntimeError):
            game.play(jim, jim.deal(1))

    def test_selcting_answer_ups_score(self):
        game, bob, joe, jim = setup_basic_game()
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        game.winner(bob, [0])
        total_score = joe.points + jim.points
        self.assertEqual(1, total_score)
        
    def test_selecting_answer_moves_czar(self):
        game, bob, joe, jim = setup_basic_game()
        game.play(jim, jim.deal(2))
        game.play(joe, joe.deal(1))
        game.winner(bob, [0])
        self.assertEqual(joe, game.czar)


class ParserTest(unittest.TestCase):
    def test_basic_command_works(self):
        game = gameclass.Game()
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual('start', p.command)

    def test_one_argument_command_works(self):
        game = gameclass.Game()
        cmdstring = 'winner 1'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)

    # note weird hacky thing: there were lots of tests that depend upon
    # play returning a number, but play actually needs to return cards.
    # so, there are two different behaviors going here: the play cmd,
    # without a player, just returns numbers.  with a player, it
    # expands out to cards.  we will only use the player version in
    # real life, but the numbers version is handy for testing.

    # thinking these tests all need to use a CAHmsg instead of a string
    # for the cmdstring argument.  that way, they have a msg.source for
    # the parser to work with, as well as a nick to know who's
    # speaking.

    def test_multi_argument_command(self):
        game = gameclass.Game()
        cmdstring = 'play 3 4 5'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual('play', p.command)
        self.assertEqual([3, 4, 5], p.args)

    def test_one_arg_with_garbage(self):
        game = gameclass.Game()
        cmdstring = 'winner 1 because we rock'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)

    def test_multi_arg_with_garbage(self):
        game = gameclass.Game()
        cmdstring = 'play 1 2 3 because ew'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual('play', p.command)
        self.assertEqual([1, 2, 3], p.args)

    def test_random_string(self):
        game = gameclass.Game()
        cmdstring = 'why is the sky blue?'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual(None, p.command)
        self.assertEqual([], p.args)

    def test_cmd_no_args(self):
        game = gameclass.Game()
        cmdstring = 'pick yourself up'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual(None, p.command)
        self.assertEqual([], p.args)

    def test_pick_works_as_play(self):
        game = gameclass.Game()
        game.status = 'wait_answers'
        cmdstring = 'pick 1'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual('play', p.command)
        self.assertEqual([1], p.args)

    def test_pick_works_as_winner(self):
        game = gameclass.Game()
        game.status = 'wait_czar'
        cmdstring = 'pick 1'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual('winner', p.command)
        self.assertEqual([1], p.args)

    def test_shame_works_as_score(self):
        game = gameclass.Game()
        cmdstring = 'shame'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        self.assertEqual('score', p.command)
        game.status = 'wait_czar'
        p.parse(msg)
        self.assertEqual('score', p.command)

    def test_dealing_a_card_works(self):
        game, bob, joe, jim = setup_basic_game()
        jimcard = jim.show_hand()[1]
        cmdstring = 'play 1'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertEqual([jimcard], game.answers[jim]['cards'])

    def test_dealing_inorder_cards_works(self):
        game, bob, joe, jim = setup_basic_game()
        jimcards = jim.show_hand()[1:4]
        cmdstring = 'play 1 2 3'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertEqual(jimcards, game.answers[jim]['cards'])

    def test_dealing_wackorder_cards_works(self):
        game, bob, joe, jim = setup_basic_game()
        jimcards = []
        jimcards.append(jim.show_hand()[3])
        jimcards.append(jim.show_hand()[1])
        jimcards.append(jim.show_hand()[7])
        cmdstring = 'play 3 1 7'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertEqual(jimcards, game.answers[jim]['cards'])

    def test_dupe_names_fail(self):
        game, bob, joe, jim = setup_basic_game()
        cmdstring = 'join'
        # oops, we've already got a bob here...
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        config = Config()
        channel = config.data['default_channel']
        text = config.data['text']['en']['double_join']
        expected = call(channel, text)
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])


class ConfigTest(unittest.TestCase):
    def test_config_exists_at_all(self):
        config = Config()
        self.assertEqual(['.', '..'], config.path)

    def test_config_reads_default_file(self):
        config = Config()
        self.assertEqual('cards', config.data['carddir'])


class GameChatTest(unittest.TestCase):
    def setUp(self):
        gameclass.chat.Chat.say.reset_mock()

    def test_chat_says_something(self):
        config = Config()
        chan = config.data['default_channel']
        text = config.data['text']['en']['round_start']
        game = gameclass.Game()
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(chan, text)
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[0])

    def test_cards_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']

        # first, when no game is running
        game = gameclass.Game()
        cmdstring = 'cards'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, game.get_text('game_not_started'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # then, with a real game going
        text = config.data['text']['en']['player_hand']
        game, bob, joe, jim = setup_basic_game()
        cmdstring = 'cards'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        hand = joe.show_hand()
        handstring = ' '.join(['[{}] {}'.format(i, card)
            for i, card
            in enumerate(hand)])
        text = text.format(cards=handstring)
        expected = call('Joe', text)
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

    def test_commands_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']
        game, bob, joe, jim = setup_basic_game()
        cmdstring = 'commands'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, CmdParser(game).get_commands())
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

    def test_help_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']
        help_blurb = config.data['text']['en']['help_blurb']
        game, bob, joe, jim = setup_basic_game()
        cmdstring = 'help'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, help_blurb)
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

    # TODO: write a test to exercise joining before the game starts, which
    # seems to work, but shouldn't

    def test_join_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']
        welcome_wait = config.data['text']['en']['welcome_wait']
        num = 2
        player_word = 'players' if num > 1 else 'player'
        welcome_wait = welcome_wait.format(name='Bob', num=num, 
            player_word=player_word)
        game = gameclass.Game()

        # first attempt to join
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, welcome_wait)
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # second attempt to join (different message)
        double_join = config.data['text']['en']['double_join']
        cmdstring = 'join'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p.parse(msg)
        game.command(p)
        expected = call(channel, double_join)
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # third player joins
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        welcome_start = config.data['text']['en']['welcome_start']
        welcome_start = welcome_start.format(name='Jim')
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, welcome_start)
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[4])

    def test_list_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']
        game, bob, joe, jim = setup_basic_game()
        cmdstring = 'list'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertTrue(re.search("Players currently in the game:", 
            str(gameclass.chat.Chat.say.mock_calls[-1])))

    def test_play_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']
        game, bob, joe, jim = setup_basic_game()

        # 'czar can't play' message
        cmdstring = 'play 1'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        with self.assertRaises(RuntimeError):
            game.command(p)
        expected = call(channel, game.get_text('not_player'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # normal player plays
        cmdstring = 'play 1'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        answer = game.format_answer(game.answers[joe]['cards'])
        expected = call('Joe', 
            game.get_text('answer_played').format(answer=answer))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # normal player erroneously plays again
        cmdstring = 'play 2'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        with self.assertRaises(RuntimeError):
            game.command(p)
        answer = game.format_answer(game.answers[joe]['cards'])
        expected = call(channel, game.get_text('already_played'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # final player plays
        cmdstring = 'play 2'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, game.get_text('all_cards_played'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-4])

    def test_quit_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']
        game, bob, joe, jim = setup_basic_game()

        # normal quit
        cmdstring = 'quit'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, 
                        game.get_text('quit_message').format(player='Bob'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # game-ending quit
        cmdstring = 'quit'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, game.get_text('game_start'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

    def test_reload_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']

        # reloading outside a running game works properly
        game = gameclass.Game()
        cmdstring = 'reload'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, game.get_text('reload_announcement'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # reload during a game tells you to wait
        game, bob, joe, jim = setup_basic_game()
        cmdstring = 'reload'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, game.get_text('reload_wait'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

    def test_score_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']
        game, bob, joe, jim = setup_basic_game()
        bob.points = 3
        joe.points = 2
        jim.points = 5
        cmdstring = 'score'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertTrue(re.search("The most horrible people:", 
            str(gameclass.chat.Chat.say.mock_calls[-1])))

    def test_start_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']
        game, bob, joe, jim = setup_basic_game()
        # the initial "start" command is already issued in setup_basic_game(),
        # and is accounted for in all the various tests that use it
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, game.get_text('game_already_started'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

    def test_state_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']

        # inactive state
        game = gameclass.Game()
        cmdstring = 'state'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, game.get_text('status')['inactive'])
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # waiting for players
        bob = Player('Bob')
        joe = Player('Joe')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        cmdstring = 'state'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, 
            game.get_text('status')['wait_players'].format(num=1))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # wait_answers state
        jim = Player('Jim')
        game.add_player(jim)
        cmdstring = 'state'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        players = "Jim and Joe"
        question = game.question.formattedvalue
        expected = call(channel, 
            game.get_text('status')['wait_answers'].format(players=players,
                                                           question=question))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # wait_czar state
        cmdstring = 'play 1'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        cmdstring = 'state'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, 
            game.get_text('status')['wait_czar'].format(czar='Bob'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-4])

    def test_winner_command_uses_chat(self):
        config = Config()
        channel = config.data['default_channel']

        # setup for a non-czar to try picking the winner
        game, bob, joe, jim = setup_basic_game()
        cmdstring = 'play 1'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        cmdstring = 'play 1'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        cmdstring = 'winner 0'
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        expected = call(channel, game.get_text('not_czar'))
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-1])

        # now the czar picks
        cmdstring = 'winner 0'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertTrue(re.search('Winner is: ', 
                                  str(gameclass.chat.Chat.say.mock_calls[-5])))
        text = game.get_text('round_announcement')
        text = text.format(round_num=2, czar='Joe')
        expected = call(channel, text)
        self.assertEqual(expected, gameclass.chat.Chat.say.mock_calls[-4])



class ResponseTest(unittest.TestCase):
    def setUp(self):
        gameclass.chat.Chat.say.reset_mock()

    def test_round_num_displays(self):
        game = gameclass.Game()
        game, bob, joe, jim = setup_basic_game()
        self.assertTrue(re.search("Round 1!",
            str(gameclass.chat.Chat.say.mock_calls[4])))
        self.assertTrue(re.search("Bob is the card czar",
            str(gameclass.chat.Chat.say.mock_calls[4])))

    def test_answers_are_displayed(self):
        # TODO: this test is incomplete
        game = gameclass.Game()
        game, bob, joe, jim = setup_basic_game()
        question = game.question
        game.play(joe, joe.deal(1))
        game.play(jim, jim.deal(1))


if __name__ == '__main__':
    unittest.main()
