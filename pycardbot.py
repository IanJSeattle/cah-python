# vi: set et ai wm=0:

import sys
import logging
import game
from config import Config
import cmdparser as p

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    maingame = None
    try:
        logger.info('Establishing IRC connection')
        maingame = game.Game()
    except KeyboardInterrupt:
        if maingame:
            maingame.irc.say('Shutting down. Thanks for playing!')
        logger.info('shutting down by keyboard interrupt')
        print('Shutting down')


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


if __name__ == '__main__':
    main()
