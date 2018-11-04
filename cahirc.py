# vi: set ai wm=0 ts=4 sw=4 et:
""" provides IRC services for the CAH bot. depends upon the irc library. """

import logging
import irc.bot
import irc.strings
from irc.client import Event, NickMask
from config import Config
from player import Player
from main import receive_msg
import cmdparser as p

logger = logging.getLogger(__name__)

class Cahirc(irc.bot.SingleServerIRCBot):
    def __init__(self, game):
        config = Config().data
        self.game = game
        self.parser = p.CmdParser(game)
        port = config['port'] if 'port' in config else 6667
        nickname = config['my_nick']
        server = config['server']
        port = config['port']
        super().__init__([(server, port)], nickname, nickname)
        self.channel = config['default_channel']
        self.destination = self.channel
        self.started = False

    #------------------------------------------------------------
    # IRC bot functions
    #------------------------------------------------------------

    def start(self):
        if not self.started:
            logger.info('Starting IRC subsystem')
            self.started = True
            super().start()

    def on_nicknameinuse(self, connection, event):
        nick = connection.get_nickname()
        newnick = nick + '_'
        #logger.info(f'Nickname "{nick}" already in use, trying "{newnick}"')
        logger.info('Nickname "{}" already in use, trying "{}"'
                    .format(nick, newnick))
        connection.nick(newnick)

    def on_welcome(self, connection, event):
        #logger.info(f'Joining {self.channel}')
        logger.info('Joining {}'.format(self.channel))
        connection.join(self.channel)

    def on_privmsg(self, connection, event):
        receive_msg(self.game, IRCmsg(event))

    def on_pubmsg(self, connection, event):
        receive_msg(self.game, IRCmsg(event))

    #------------------------------------------------------------
    # CAH specific functions
    #------------------------------------------------------------

    def say(self, text):
        """ recipient is either the channel name, or the nick for a privmsg """
        #logger.debug(f'Sending to {self.destination}: {text}')
        logger.debug('Sending to {}: {}'.format(self.destination, text))
        self.connection.privmsg(self.destination, text)


class IRCmsg(object):
    """ message object to simplify message passing """
    def __init__(self, event):
        self.nick = event.source.nick
        self.user = event.source.user
        self.msg = event.arguments[0]
        self.source = event.type
        #logger.debug(f'Got {self.source} from {self.nick}: {self.msg}')
        logger.debug('Got {} from {}: {}'.format(self.source, self.nick, 
                                                 self.msg))

    def make_player(self):
        return Player(self.nick, self.user)


class FakeIRCmsg(IRCmsg):
    """ only used for testing.  it can take either a well formed user string
    (see default user argument) or a Player object.  poorly formed strings will
    cause problems, so don't do that. """
    def __init__(self, string, user='Bob!~bobbo@127.0.0.1', source='pubmsg'):
        if isinstance(user, Player):
            user = '{}!{}@127.0.0.1'.format(user.nick, user.user)
        mask = NickMask(user)
        source = '#test' if source == 'pubmsg' else mask.nick
        event = Event('privmsg', mask, source, [string])
        super().__init__(event)
