import re
import json
from mmpy_bot.bot import listen_to
from mmpy_bot.dispatcher import Message

# had a thought to use this var to do msg.reply() calls with data coming
# from the game.  may or may not be a good idea.
MESSAGE = None

def msg2game(msg):
    """ open the pipe and write out our message to the cah game """
    MESSAGE = msg
    with open(filename, 'w') as fstream:
        fstream.write(msg._body)


@listen_to('test message')
def hello(message):
    message.reply('message received **wink**')
    #msg2game(message)
