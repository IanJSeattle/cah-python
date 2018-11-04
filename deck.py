# vi: set expandtab ai:

from random import shuffle
import json
from card import Card
from exceptions import NoMoreCards

class Deck(object):
    """ a Deck represents a set of cards, and may contain either
    Question or Answer cards, accessed via an argument to the deal()
    method. this simplifies reading in cards from files. """

    def __init__(self, cards=None):
        """ self.cards is an array of Card objects """
        self.answercards = []
        self.questioncards = []
        if cards != None:
            for thiscard in cards:
                self.add(thiscard)
        self.dealt_answers = []
        self.dealt_questions = []

    def add(self, thiscard):
        """ add a Card to the Deck """
        if thiscard.cardtype == 'Answer':
            self.answercards.append(thiscard)
        else:
            self.questioncards.append(thiscard)

    def deal(self, cardtype, num=None):
        """ return one Card from the Deck, removing it from available
        cards, and putting it in the appropriate dealt card stack. """
        if cardtype == 'Answer':
            if num is None:
                card = self.answercards.pop()
            else:
                card = self.answercards.pop(num)
            self.dealt_answers.append(card)
        else:
            if num is None:
                try:
                    card = self.questioncards.pop()
                except IndexError:
                    raise NoMoreCards
            else:
                card = self.questioncards.pop(num)
            self.dealt_questions.append(card)
        return card

    def shuffle(self):
        """ shuffle all the Cards in the Deck """
        shuffle(self.answercards)
        shuffle(self.questioncards)

    def __len__(self):
        """ special function for length,  """
        return len(self.questioncards) + len(self.answercards)

    def read_in(self, filename):
        with open(filename) as fp:
            cards = json.load(fp)

            for tmpcard in cards:
                newcard = Card(tmpcard['type'], tmpcard['value'])
                newcard.pick = tmpcard['pick']
                newcard.draw = tmpcard['draw']
                newcard.source = tmpcard['source']
                self.add(newcard)

    def show_hand(self, cardtype):
        if cardtype == 'Answer':
            return [card.value for card in self.answercards]
        else:
            return [card.value for card in self.questioncards]

    def reset(self):
        self.answercards += self.dealt_answers
        self.dealt_answers = []
        self.questioncards += self.dealt_questions
        self.dealt_questions = []

    def undeal_last(self, cardtype):
        """
        "undeal" the last card back into active cards.  used when a
        player does a double-play.  stupid, but necessary since the
        CmdParser is what's currently doing the dealing, so the Game
        can't prevent the second deal().
        """
        if cardtype == 'Answer':
            card = self.dealt_answers.pop()
            self.answercards.append(card)
        elif cardtype == 'Question':
            card = self.dealt_questions.pop()
            self.questioncards.append(card)
