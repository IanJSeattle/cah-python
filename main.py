# vi: set expandtab ai:

from player import Player
from card import Card
from deck import Deck
import os
import config

def load_cards():
    currdir = os.getcwd()
    os.chdir(config.CONFIG['carddir'])
    files = os.listdir()
    thisdeck = Deck()
    for thisfile in files:
        if not thisfile.endswith('json'):
            continue
        thisdeck.read_in(thisfile)
    os.chdir(currdir)
    return thisdeck
        
    
def main():
    thisdeck = load_cards()
    thisdeck.shuffle()
    newcard = thisdeck.deal('Answer')
    print(thisdeck.get_cards('Question'))

main()
