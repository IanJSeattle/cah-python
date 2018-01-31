#!/usr/bin/env python
# vi: set ai wm=0 ts=4 sw=4 et:
#
# Example program using irc.bot.
#
# based on code by Joel Rosdahl <joel@rosdahl.net>

import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr, Event, NickMask
from config import Config
from player import Player

class Cahirc(irc.bot.SingleServerIRCBot):
    def __init__(self, game):
        config = Config().data
        port = config['port'] if 'port' in config else 6667
        super().__init__([(config['server'], port)], config['my_nick'], 
            config['my_nick'])
        self.channel = config['default_channel']
        self.game = game

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, event):
        tell_game(self, c, event)

    def on_pubmsg(self, c, event):
        tell_game(self, c, event)

    def tell_game(self, c, event):
        nick = event.source.nick
        user = event.source.user
        game.receive_irc(str(event.type), nick, user, str(event.arguments[0]))

    def say(self, recipient, text):
        self.connection.privmsg(recipient, text)

    # some other process will have to call irc.start(), i guess


class IRCmsg(object):
    def __init__(self, event):
        self.nick = event.source.nick
        self.user = event.source.user
        self.msg = event.arguments[0]
        self.source = event.type


class fakeIRCmsg(IRCmsg):
    def __init__(self, string, user='Bob!~bobbo@127.0.0.1'):
        if isinstance(user, Player):
            user = '{}!{}@127.0.0.1'.format(user.nick, user.user)
        nm = NickMask(user)
        event = Event('privmsg', nm, '#test', [string])
        super().__init__(event)
