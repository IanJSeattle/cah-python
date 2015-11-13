#!/usr/bin/env python
# vi:set expandtab ai:

import unittest, sys

sys.path.append('..')

from card import Card
from deck import Deck

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

if __name__ == '__main__':
    unittest.main()
