# vi: set expandtab ai:

import os
from config import Config
from player import Player
from card import Card
from deck import Deck
from game import Game


def main():
    game = Game()
    parser = CmdParser(game)



if __name__ == '__main__':
    main()
