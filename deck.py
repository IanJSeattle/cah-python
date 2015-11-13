# vi: set expandtab ai:

from random import shuffle
from card import Card
import json

class Deck(object):
    """ a Deck represents a set of cards, and may contain either
    Question or Answer cards, accessed via an argument to the deal()
    method. """

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
        return True

    def deal(self, cardtype='Question', num=None):
        """ return one Card from the Deck """
        if cardtype == 'Answer':
            if num == None:
                card = self.answercards.pop()
            else:
                card = self.answercards.pop(num)
            self.dealt_answers.append(card)
        else:
            if num == None:
                card = self.questioncards.pop()
            else:
                card = self.questioncards.pop(num)
            self.dealt_questions.append(card)
        return card

    def shuffle(self):
       """ shuffle all the Cards in the Deck """
       shuffle(self.answercards) 
       shuffle(self.questioncards) 
       return True

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
    
    def show_hand(self, cardtype='Question'):
        if cardtype == 'Answer':
            return [card.value for card in self.answercards]
        else:
            return [card.value for card in self.questioncards]
