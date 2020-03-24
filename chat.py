""" this module sets up a generic chat interface, to the extent
possible.  it will specifically allow for either irc or mattermost to be
used agnostically.  other chat systems aren't currently in spec, but by
attempting to be generic and allowing dialect modules to be used, it
should be relatively easy to adapt for other chat systems. """

import json
import config
from game import Game
import cmdparser as p


class CAHmsg:
    """ message object """
    def __init__(self, nick, message, source):
        self.nick = nick
        self.message = message
        self.source = source

    def __repr__(self):
        return f'CAHmsg("{self.nick}", "{self.message}", "{self.source}")'

    def json(self):
        return json.dumps({'nick': self.nick, 
                           'message': self.message,
                           'source': self.source})


class Chat:
    """
    module to allow generic access to chat systems.  this depends
    upon imported dialect modules implementing the same interface.
    allowed dialects:
    
    * irc
    * mattermost
    """

    def __init__(self, dialect: str, game: Game):
        """ set up which type of interface we're using """
        if dialect == 'irc':
            import cahirc
            self.system = cahirc.Cahirc(game)
        elif dialect == 'mattermost':
            import cahmm
            self.system = cahmm.Cahmm(game)
        self.config = config.Config().data
        self.game = game
        # we expect start() to do everything with the chat system
        # necessary to be ready to start sending and receiving messages
        # with the system.  the system should furthermore handle
        # reconnecting autonomously.
        self.system.start()

    def say(self, destination: str, text: str) -> None:
        """ say something to the requested destination.  destination
        should be either an individual identifier (for a direct message
        to a person) or a channel name. """
        self.system.say(destination, text)

    def receive_msg(self, msg: CAHmsg):
        """ function to process an incoming message. the msg variable
        should contain a CAHmsg object.  """
        parser = p.CmdParser(self.game)
        parser.parse(msg)
        self.game.command(parser)
