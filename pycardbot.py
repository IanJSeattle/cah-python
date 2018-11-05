# vi: set et ai wm=0:

import signal
import sys
import logging
import game
from config import Config
import cmdparser as p

logger = logging.getLogger(__name__)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGKILL, signal_handler)
    setup_logging()
    logger.info('Establishing IRC connection')
    return game.Game()


def setup_logging():
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        level = logging.DEBUG
    else:
        level = logging.INFO
    config = Config().data
    logging.basicConfig(filename=config['logfile'],
                        level=level,
                        format='%(asctime)s %(levelname)s: %(message)s')


def receive_msg(currgame, msg):
    parser = p.CmdParser(currgame)
    parser.parse(msg)
    currgame.command(parser)


def signal_handler(sig, frame):
    logger.info('Shutting down from signal')
    if maingame:
        logger.info('Sending shutdown message via IRC')
        lang = Config().data['language']
        shutdown_message = Config().data['text'][lang]['shutdown_message']
        maingame.irc.say(shutdown_message)
        maingame.irc.die('Shutting down')
    else:
        logger.info('Unable to send shutdown message via IRC')
    sys.exit(0)


if __name__ == '__main__':
    maingame = main()
    maingame.irc.start() # start call never returns
