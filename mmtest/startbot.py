"""

left off here: reading from both FIFOs works like it should.  now need
to take the received messages and make them do something.  in the case
of messages bound toward the game, figure out how to call
receive_msg().  in the case of messages bound for mattermost, figure
out how to do a message.reply() with the data we have from the game.

to demonstrate current state, start this program, and in another
window:

cat game-sample > game2mm.fifo
cat mm-sample > mm2game.fifo

"""


import sys
sys.path.append('..')
from chat import CAHmsg
import json
import os
from multiprocessing import Process
from mmpy_bot import bot, settings

MM_RECV = 'mm2game.fifo'
GAME_RECV = 'game2mm.fifo'


def make_fifos():
    """ make our FIFOs if they don't already exist """
    for fifo in [MM_RECV, GAME_RECV]:
        if not os.path.exists(fifo):
            os.mkfifo(fifo)


def start_bot():
    """ start the bot going """
    b = bot.Bot()
    b.run()


def receive_mm():
    """ receive messages from mattermost """
    while True:
        with open(MM_RECV, 'r') as fstream:
            data = json.load(fstream)
            source = 'pubmsg'
            if data['message_type'] == 'D':
                source = 'privmsg'
            message = CAHmsg(data['data']['sender_name'], 
                             data['data']['post']['message'], 
                             source)
            # replace this with something that invokes # chat.receive_msg()
            print(message)


def receive_game():
    """ receive messages from the game engine """
    while True:
        with open(GAME_RECV, 'r') as fstream:
            data = json.load(fstream)
            message = CAHmsg(**data)
            # replace this with something that writes out to the mm channel
            print(message)


def main():
    print('starting mattermost transciever, 10-4 good buddy')
    make_fifos()
    p = Process(target=start_bot)
    p.start()
    rmm = Process(target=receive_mm)
    rmm.start()
    rg = Process(target=receive_game)
    rg.start()

if __name__ == '__main__':
    main()
