# vi: set ai wm=0 ts=4 sw=4 et:
""" provides IRC services for the CAH bot. depends upon the irc library. """

import logging
import threading
import irc.bot
import irc.strings
from irc.client import Event, NickMask
from config import Config
from player import Player
from pycardbot import receive_msg
import cmdparser as p
from util import logtime
import chat

logger = logging.getLogger(__name__)

class Cahirc(irc.bot.SingleServerIRCBot):
    def __init__(self, game):
        config = Config().data
        self.game = game
        self.parser = p.CmdParser(game)
        port = config['port'] if 'port' in config else 6667
        nickname = config['chat']['irc']['my_nick']
        self.server = config['chat']['irc']['server']
        self.port = config['chat']['irc']['port']
        super().__init__([(self.server, self.port)], nickname, nickname)
        self.channel = config['chat']['irc']['default_channel']
        self.started = False

    #------------------------------------------------------------
    # IRC bot functions
    #------------------------------------------------------------

    def ping(self):
        logger.info(f'PING {self.server}')
        ping_interval = self.game.config['chat']['irc']['ping_interval']
        self.connection.ping(self.server)
        threading.Timer(ping_interval, self.ping).start()

    def start(self):
        if not self.started:
            logger.info(f'IRC connecting to {self.server}:{self.port}')
            self.started = True
            super().start()
            logger.info('IRC started')
            threading.Timer(20, self.ping).start()

    def stop(self, text):
        self.die(text)

    def on_nicknameinuse(self, connection, event):
        nick = connection.get_nickname()
        newnick = nick + '_'
        logger.info('Nickname "{}" already in use, trying "{}"'
                    .format(nick, newnick))
        connection.nick(newnick)

    def on_welcome(self, connection, event):
        logger.info('Joining {}'.format(self.channel))
        connection.join(self.channel)
        self.say(self.channel, self.game.get_text('game_start'))

    def on_privmsg(self, connection, event):
        self.game.chat.receive_msg(chat.CAHmsg(event.source.nick, event.arguments[0], event.type))

    def on_pubmsg(self, connection, event):
        self.game.chat.receive_msg(chat.CAHmsg(event.source.nick, event.arguments[0], event.type))

    #------------------------------------------------------------
    # CAH specific functions
    #------------------------------------------------------------

    @logtime
    def say(self, destination, text):
        """ recipient is either the channel name, or the nick for a privmsg """
        logger.debug('Sending to {}: {}'.format(destination, text))
        self.connection.privmsg(destination, text)


class IRCmsg(object):
    """ message object to simplify message passing """
    def __init__(self, event):
        self.nick = event.source.nick
        self.user = event.source.user
        self.msg = event.arguments[0]
        self.source = event.type
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
