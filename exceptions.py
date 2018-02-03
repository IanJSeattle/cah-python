# vi: set et:
"""
exceptions used in the game
"""

class NoMoreCards(Exception):
    """
    this exception is raised when requesting a Card from a Deck, but no
    more Cards remain to be dealt.
    """

class NotPermitted(Exception):
    """
    this exception indicates that the requested action is not
    permitted, such as playing multiple cards in one round, or the czar
    trying to play a card.
    """
