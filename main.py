# vi: set expandtab ai:

import os
from config import Config
from player import Player
from card import Card
from deck import Deck
from game import Game


def main():
    game = Game()
    parser = CmdParse(game)
    # how is an IRC nick turned into a Player name?


if __name__ == '__main__':
    main()
